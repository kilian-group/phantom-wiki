import argparse
import asyncio
import json
import logging
import math
import tempfile
from copy import deepcopy
from pathlib import Path

import pandas as pd

from phantom_wiki.facts.database import Database

from . import constants, get_parser
from ._types import Conversation, LLMChatResponse
from .agents import get_agent
from .agents.common import Agent
from .llm import InferenceGenerationConfig, LLMChat, get_llm, is_huggingface_model
from .prolog_utils import get_prolog_results
from .prompts import (
    ACT_EXAMPLES,
    COT_EXAMPLES,
    COT_EXAMPLES_PROLOG,
    FEWSHOT_EXAMPLES,
    FEWSHOT_EXAMPLES_PROLOG,
    REACT_EXAMPLES,
    LLMPrompt,
    get_llm_prompt,
)
from .utils import load_data, setup_logging

logger = logging.getLogger(__name__)


def get_model_kwargs(args: argparse.Namespace) -> dict:
    match args.model_name:
        case model_name if is_huggingface_model(model_name):
            model_kwargs = dict(
                model_path=args.model_path,
                max_model_len=args.inf_vllm_max_model_len,
                tensor_parallel_size=args.inf_vllm_tensor_parallel_size,
                # If the method is zeroshot or fewshot, we do not need to use the API (for vLLM)
                # This can be overridden by setting `use_api=True` in the model_kwargs.
                # NOTE: non-vLLM models will always use the API so this flag doesn't affect them.
                use_api=(
                    args.method
                    in [
                        # "zeroshot-rag", "fewshot-rag", "cot-rag",
                        "react",
                        "act",
                        "react->cot-sc",
                        "cot-sc->react",
                    ]
                ),
                port=args.inf_vllm_port,
            )
        case _:
            model_kwargs = dict(
                model_path=args.model_path,
                usage_tier=args.inf_usage_tier,
            )
    return model_kwargs


def get_agent_kwargs(args: argparse.Namespace) -> dict:
    match args.method:
        case "zeroshot":
            agent_kwargs = dict(prolog_query=args.prolog_query)
        case "fewshot":
            agent_kwargs = dict(
                fewshot_examples=FEWSHOT_EXAMPLES if not args.prolog_query else FEWSHOT_EXAMPLES_PROLOG,
                prolog_query=args.prolog_query,
            )
        case "zeroshot-sc":
            agent_kwargs = dict(
                num_votes=args.sc_num_votes, sep=constants.answer_sep, prolog_query=args.prolog_query
            )
        case "fewshot-sc":
            agent_kwargs = dict(
                num_votes=args.sc_num_votes,
                sep=constants.answer_sep,
                fewshot_examples=FEWSHOT_EXAMPLES,
                prolog_query=args.prolog_query,
            )
        case "cot":
            agent_kwargs = dict(
                cot_examples=COT_EXAMPLES if not args.prolog_query else COT_EXAMPLES_PROLOG,
                prolog_query=args.prolog_query,
            )
        case "cot-sc":
            agent_kwargs = dict(
                cot_examples=COT_EXAMPLES,
                num_votes=args.sc_num_votes,
                sep=constants.answer_sep,
            )
        case "zeroshot-rag":
            agent_kwargs = dict(
                embedding_model_name=args.retriever_method,
                retriever_num_documents=args.retriever_num_documents,
            )
        case "fewshot-rag":
            agent_kwargs = dict(
                embedding_model_name=args.retriever_method,
                retriever_num_documents=args.retriever_num_documents,
                fewshot_examples=FEWSHOT_EXAMPLES,
            )
        case "cot-rag":
            agent_kwargs = dict(
                embedding_model_name=args.retriever_method,
                retriever_num_documents=args.retriever_num_documents,
                cot_examples=COT_EXAMPLES,
            )
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
        case "react->cot-sc":
            # Provide the second llm prompt (CoTSC) as an agent kwarg
            agent_kwargs = dict(
                max_steps=args.react_max_steps,
                react_examples=REACT_EXAMPLES,
                cot_llm_prompt=get_llm_prompt("cot-sc", args.model_name),
                cot_examples=COT_EXAMPLES,
                num_votes=args.sc_num_votes,
                sep=constants.answer_sep,
                # react uses args.inf_temperature, cot-sc uses this hardcoded value
                cotsc_inf_temperature=constants.inf_temperature_hi,
            )
        case "cot-sc->react":
            # Provide the second llm prompt (React) as an agent kwarg
            agent_kwargs = dict(
                cot_examples=COT_EXAMPLES,
                num_votes=args.sc_num_votes,
                sep=constants.answer_sep,
                # react uses args.inf_temperature, cot-sc uses this hardcoded value
                cotsc_inf_temperature=constants.inf_temperature_hi,
                react_llm_prompt=get_llm_prompt("react", args.model_name),
                max_steps=args.react_max_steps,
                react_examples=REACT_EXAMPLES,
            )
        case _:
            agent_kwargs = dict()
    return agent_kwargs


async def main(args: argparse.Namespace) -> None:
    logger.info(f"Loading LLM='{args.model_name}'")
    model_kwargs = get_model_kwargs(args)
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
        logger.info(f"Running inference for method='{args.method}' with {seed=}")
        for split in args.split_list:
            dataset = load_data(args.dataset, split, args.from_local)
            logger.info(f"Loading dataset='{args.dataset}' :: {split=}")
            df_qa_pairs = pd.DataFrame(dataset["qa_pairs"])
            df_text = pd.DataFrame(dataset["text"])

            # Construct agent for the data split
            agent_kwargs = get_agent_kwargs(args)
            agent: Agent = get_agent(
                args.method,
                text_corpus=df_text,
                llm_prompt=llm_prompt,
                agent_kwargs=agent_kwargs,
            )

            if args.prolog_query:
                logger.info("Loading Prolog database")
                # Create temporary file and load database from disk
                with tempfile.NamedTemporaryFile(mode="w", suffix=".pl") as tmp:
                    content = dataset["database"]["content"]
                    tmp.write("\n".join(content))
                    tmp.flush()
                    db = Database.from_disk(tmp.name)

            # If the model is a local LLM, we can run on all QA examples
            num_df_qa_pairs = len(df_qa_pairs)

            if args.batch_number is not None:
                assert args.batch_number >= 1, "Batch number must be >= 1"
                assert args.batch_number <= math.ceil(
                    num_df_qa_pairs / args.batch_size
                ), "Batch number must be <= ceil(num_df_qa_pairs / batch_size)"
                batch_size = args.batch_size
            else:
                can_process_full_batch = is_huggingface_model(args.model_name) and (
                    args.method not in ["react", "act", "react->cot-sc", "cot-sc->react"]
                )
                batch_size = num_df_qa_pairs if can_process_full_batch else args.batch_size
            for batch_number in range(1, math.ceil(num_df_qa_pairs / batch_size) + 1):
                run_name = (
                    f"split={split}"
                    + f"__model_name={args.model_name.replace('/', '--')}"
                    + f"__bs={batch_size}"
                    + f"__bn={batch_number}"
                    + f"__seed={seed}"
                )
                pred_path = Path(args.output_dir) / "preds" / args.method / f"{run_name}.json"

                # Skip if the batch number is not the one specified
                if (args.batch_number is not None) and (batch_number != args.batch_number):
                    continue
                # Skip if the output file already exists and --force is not set
                if pred_path.exists() and not args.force:
                    logger.info(f"Skipping {pred_path} as it already exists. Use --force to overwrite.")
                    continue

                # Get batch
                batch_start_idx = (batch_number - 1) * batch_size
                batch_end_idx = batch_start_idx + batch_size
                logger.info(
                    f"Getting predictions for questions [{batch_start_idx}, {batch_end_idx}) "
                    f"out of {num_df_qa_pairs}"
                )
                batch_df_qa_pairs = df_qa_pairs.iloc[batch_start_idx:batch_end_idx]

                # Run the method and get final responses for the batch
                # In zeroshot, fewshot, the LLM responds with the final answer in 1 turn only,
                # so they support batch async inference
                agent_interactions = None
                match args.method:
                    case (
                        "zeroshot" | "zeroshot-sc" | "fewshot" | "fewshot-sc" | "zeroshot-rag" | "fewshot-rag"
                    ):
                        questions: list[str] = batch_df_qa_pairs["question"].tolist()
                        inf_gen_config = default_inf_gen_config.model_copy(update=dict(seed=seed), deep=True)
                        responses: list[LLMChatResponse] = await agent.batch_run(
                            llm_chat, questions, inf_gen_config
                        )
                        # NOTE: the agent interactions are just single Conversation objects containing the
                        # prompt for the self-consistency methods, we save the Conversation object from the
                        # last iteration
                        agent_interactions: list[Conversation] = agent.agent_interactions
                    case "cot" | "cot-sc" | "cot-rag":
                        questions: list[str] = batch_df_qa_pairs["question"].tolist()
                        inf_gen_config = default_inf_gen_config.model_copy(update=dict(seed=seed), deep=True)
                        responses: list[LLMChatResponse] = await agent.batch_run(
                            llm_chat, questions, inf_gen_config
                        )
                        agent_interactions: list[Conversation] = agent.agent_interactions
                    # case "zeroshot-rag":
                    #     raise NotImplementedError("RAG evaluation is not supported yet.")
                    case "react" | "act" | "react->cot-sc" | "cot-sc->react":
                        # Run all agents in parallel using asyncio.gather
                        responses: list[LLMChatResponse] = []
                        inf_gen_config = default_inf_gen_config.model_copy(update=dict(seed=seed), deep=True)
                        agents = [deepcopy(agent) for _ in range(batch_size)]
                        responses = await asyncio.gather(
                            *[
                                agent.run(llm_chat, qa_sample.question, inf_gen_config)
                                for agent, qa_sample in zip(agents, batch_df_qa_pairs.itertuples())
                            ]
                        )
                        agent_interactions: list[Conversation] = [
                            agent.agent_interactions for agent in agents
                        ]

                # Process Prolog queries if needed
                prolog_results = []
                if args.prolog_query:
                    prolog_results = get_prolog_results(
                        responses, db, logger, args.log_level.upper() == "DEBUG"
                    )

                # Log the final answers for the batch
                pred_path.parent.mkdir(parents=True, exist_ok=True)
                logger.info(f"Saving predictions to {pred_path}")

                # Save after each batch run
                unsaveable_agent_kwargs: list[str] = ["cot_llm_prompt", "react_llm_prompt"]
                agent_kwargs_to_save = agent_kwargs.copy()
                for kw in unsaveable_agent_kwargs:
                    agent_kwargs_to_save.pop(kw, None)

                save_preds(
                    pred_path,
                    split,
                    inf_gen_config,
                    model_kwargs,
                    agent_kwargs_to_save,
                    args,
                    batch_number,
                    batch_df_qa_pairs,
                    responses,
                    prolog_results=prolog_results if args.prolog_query else None,
                    interactions=agent_interactions if not args.ignore_agent_interactions else [],
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
    prolog_results: list[dict] | None = None,
    interactions: list[Conversation] | None = None,
) -> None:
    preds = {}
    batch_size = len(batch_df_qa_pairs)

    for i, qa_sample in enumerate(batch_df_qa_pairs.itertuples()):
        uid = qa_sample.id

        # Get the appropriate prediction value and query info
        if prolog_results:
            pred_value = prolog_results[i]["final_value"]
            pred_query = prolog_results[i]["query"]
            query_results = prolog_results[i]["query_results"]
        else:
            pred_value = responses[i].pred
            pred_query = None
            query_results = None

        preds[uid] = {
            "true": qa_sample.answer,
            "pred": pred_value,
            "prolog_query": pred_query,
            "prolog_query_results": query_results if args.log_level.upper() == "DEBUG" else None,
            "error": responses[i].error,
            "interaction": interactions[i].model_dump() if interactions else [],
            "metadata": {
                "model": args.model_name,
                "dataset": args.dataset,
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
        f.flush()


if __name__ == "__main__":
    parser = get_parser()
    args = parser.parse_args()
    setup_logging(args.log_level)
    if args.prolog_query:
        assert len(args.split_list) == 1, (
            "When prolog_query is true, we can only evaluate one split at a time since only one Prolog "
            "database can be in memory at any given time due to limitations with pyswip"
        )

    # NOTE: asyncio.run should only be called once in a single Python instance.
    # Thus, any high-level function containing awaits in its implementation
    # must be marked with the `async` keyword in the function definition.
    # See also: https://proxiesapi.com/articles/how-many-times-should-asyncio-run-be-called-python
    asyncio.run(main(args))
