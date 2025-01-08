import argparse
import json
import math
import asyncio
import logging
from pathlib import Path

import pandas as pd
from tqdm import tqdm

from .utils import load_data, setup_logging
from .data import Conversation
from .llm import get_llm, VLLMChat, LLMChatResponse, LLMChat, InferenceGenerationConfig
from .agent import get_agent, Agent
from .prompts import get_llm_prompt, LLMPrompt, REACT_EXAMPLES, COT_EXAMPLES, ACT_EXAMPLES
from . import constants
from . import get_parser

logger = logging.getLogger(__name__)


async def main(args: argparse.Namespace) -> None:
    logger.info(f"Loading LLM={args.model_name}")
    match args.model_name:
        case model_name if model_name in VLLMChat.SUPPORTED_LLM_NAMES:
            model_kwargs = dict(
                model_path=args.model_path,
                max_model_len=args.inf_vllm_max_model_len,
                tensor_parallel_size=args.inf_vllm_tensor_parallel_size,
                # If the method is zeroshot or fewshot, we do not need to use the API (for vLLM)
                # This can be overridden by setting `use_api=True` in the model_kwargs.
                # NOTE: non-vLLM models will always use the API so this flag doesn't affect them.
                use_api=(args.method in ["react", "act"]),
            )
        case _:
            model_kwargs = dict(
                model_path=args.model_path,
            )
    llm_chat: LLMChat = get_llm(args.model_name, model_kwargs=model_kwargs)
    llm_prompt: LLMPrompt = get_llm_prompt(args.method, args.model_name)
    default_inf_gen_config = InferenceGenerationConfig(
        max_tokens=args.inf_max_tokens,
        temperature=args.inf_temperature,
        top_k=args.inf_top_k,
        top_p=args.inf_top_p,
        repetition_penalty=args.inf_repetition_penalty,
        max_retries=args.inf_max_retries,
        wait_seconds=args.inf_wait_seconds,
    )

    for seed in args.inf_seed_list:
        logger.info(f"Running inference for method={args.method} with {seed=}")
        for split in args.split_list:
            logger.info(f"Loading dataset {split=}")
            dataset = load_data(split)
            df_qa_pairs = pd.DataFrame(dataset["qa_pairs"])
            df_text = pd.DataFrame(dataset["text"])

            # Construct agent for the data split
            match args.method:
                case "zeroshot" | "fewshot":
                    agent_kwargs = dict()
                case "zeroshot-sc" | "fewshot-sc":
                    agent_kwargs = dict(
                        num_votes=args.sc_num_votes,
                        sep=constants.answer_sep,
                    )
                case "cot":
                    agent_kwargs = dict(
                        cot_examples=COT_EXAMPLES
                    )
                case "RAG":
                    raise NotImplementedError("RAG evaluation is not supported yet.")
                case "react":
                    agent_kwargs = dict(
                        max_steps=args.react_max_steps,
                        react_examples=REACT_EXAMPLES,
                    )
                case "act":
                    agent_kwargs = dict(
                        max_steps=args.react_max_steps,
                        act_examples=ACT_EXAMPLES,
                    )
                case _:
                    agent_kwargs = dict()
            agent: Agent = get_agent(
                args.method,
                text_corpus=df_text,
                llm_prompt=llm_prompt,
                agent_kwargs=agent_kwargs,
            )

            # If the model is a local LLM, we can run on all QA examples
            num_df_qa_pairs = len(df_qa_pairs)
            can_process_full_batch = (args.model_name in VLLMChat.SUPPORTED_LLM_NAMES) \
                and (args.method not in ["react", "act"])
            batch_size = num_df_qa_pairs if can_process_full_batch else args.batch_size
            for batch_number in range(1, math.ceil(num_df_qa_pairs/batch_size) + 1):
                # Skip if the batch number is not the one specified
                if (args.batch_number is not None) and (batch_number != args.batch_number):
                    continue

                # Get batch
                batch_start_idx = (batch_number - 1) * batch_size
                batch_end_idx = batch_start_idx + batch_size
                logger.info(f"Getting predictions for questions [{batch_start_idx}, {batch_end_idx}) out of {num_df_qa_pairs}")
                batch_df_qa_pairs = df_qa_pairs.iloc[batch_start_idx:batch_end_idx]

                # Run the method and get final responses for the batch
                # In zeroshot, fewshot, the LLM responds with the final answer in 1 turn only,
                # so they support batch async inference
                agent_interactions = None
                match args.method:
                    case "zeroshot" | "zeroshot-sc" | "fewshot" | "fewshot-sc":
                        questions: list[str] = batch_df_qa_pairs["question"].tolist()
                        inf_gen_config = default_inf_gen_config.model_copy(update=dict(seed=seed), deep=True)
                        responses: list[LLMChatResponse] = await agent.batch_run(llm_chat, questions, inf_gen_config)
                        # NOTE: the agent interactions are just single Conversation objects containing the prompt
                        # for the self-consistency methods, we save the Conversation object from the last iteration
                        if args.log_level == "DEBUG":
                            logging.warning(f"Saving prompts for method={args.method} in agent_interactions. This takes up a lot of space as the prompts can be large.")
                            agent_interactions: list[Conversation] = agent.agent_interactions
                    case "cot":
                        questions: list[str] = batch_df_qa_pairs["question"].tolist()
                        inf_gen_config = default_inf_gen_config.model_copy(update=dict(seed=seed), deep=True)
                        responses: list[LLMChatResponse] = await agent.batch_run(llm_chat, questions, inf_gen_config)
                        agent_interactions: list[Conversation] = agent.agent_interactions
                    case "RAG":
                        raise NotImplementedError("RAG evaluation is not supported yet.")
                    case "react" | "act":
                        # Run agent on each question one by one
                        responses: list[LLMChatResponse] = []
                        agent_interactions: list[Conversation] = []
                        for qa_sample in tqdm(batch_df_qa_pairs.itertuples(), total=batch_size):
                            agent.reset()  # Must reset the agent for each question
                            inf_gen_config = default_inf_gen_config.model_copy(update=dict(seed=seed), deep=True)
                            response = agent.run(llm_chat, qa_sample.question, inf_gen_config)
                            responses.append(response)
                            agent_interactions.append(agent.agent_interactions)

                # Log the final answers for the batch
                run_name = (
                    f"split={split}" \
                    + f"__model_name={args.model_name.replace('/', '--')}" \
                    + f"__bs={batch_size}" \
                    + f"__bn={batch_number}" \
                    + f"__seed={seed}"
                )
                pred_path = Path(args.output_dir) / "preds" / args.method / f"{run_name}.json"
                pred_path.parent.mkdir(parents=True, exist_ok=True)
                logger.info(f"Saving predictions to {pred_path}")

                # Save after each batch run
                save_preds(
                    pred_path,
                    split,
                    inf_gen_config,
                    model_kwargs,
                    agent_kwargs,
                    args,
                    batch_number,
                    batch_df_qa_pairs,
                    responses,
                    interactions=agent_interactions,
                )


def save_preds(
    pred_path: Path,
    split: str,
    inf_gen_config: InferenceGenerationConfig,
    model_kwargs: dict,
    agent_kwargs: dict,
    args: argparse.Namespace,
    batch_number: int,
    batch_df_qa_pairs: pd.DataFrame,
    responses: list[LLMChatResponse],
    interactions: list[Conversation] | None = None,
) -> None:
    preds = {}
    batch_size = len(batch_df_qa_pairs)
    for i, qa_sample in enumerate(batch_df_qa_pairs.itertuples()):
        uid = qa_sample.id
        preds[uid] = {
            "true" : qa_sample.answer,
            "pred" : responses[i].pred,
            "error": responses[i].error,
            "interaction": interactions[i].model_dump() if interactions else [],
            "metadata": {
                "model": args.model_name,
                "split": split,
                "batch_size": batch_size,
                "batch_number": batch_number,
                "type": int(qa_sample.type),
            },
            "inference_params": inf_gen_config.model_dump(),
            "model_kwargs": model_kwargs,
            "agent_kwargs": agent_kwargs,
            "usage": responses[i].usage,
        }

    with open(pred_path, "w") as f:
        json.dump(preds, f, indent=4)


if __name__ == "__main__":
    parser = get_parser()
    args = parser.parse_args()
    setup_logging(args.log_level)

    # NOTE: asyncio.run should only be called once in a single Python instance.
    # Thus, any high-level function containing awaits in its implementation 
    # must be marked with the `async` keyword in the function definition.
    # See also: https://proxiesapi.com/articles/how-many-times-should-asyncio-run-be-called-python
    asyncio.run(main(args))
