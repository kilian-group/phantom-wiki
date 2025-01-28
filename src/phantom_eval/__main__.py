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
from .prompts import get_llm_prompt, LLMPrompt, REACT_EXAMPLES, COT_EXAMPLES, ACT_EXAMPLES, FEWSHOT_EXAMPLES
from . import constants
from . import get_parser

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from phantom_wiki.facts.database import Database

logger = logging.getLogger(__name__)


def get_model_kwargs(args: argparse.Namespace) -> dict:
    match args.model_name:
        case model_name if model_name in VLLMChat.SUPPORTED_LLM_NAMES:
            model_kwargs = dict(
                model_path=args.model_path,
                max_model_len=args.inf_vllm_max_model_len,
                tensor_parallel_size=args.inf_vllm_tensor_parallel_size,
                # If the method is zeroshot or fewshot, we do not need to use the API (for vLLM)
                # This can be overridden by setting `use_api=True` in the model_kwargs.
                # NOTE: non-vLLM models will always use the API so this flag doesn't affect them.
                use_api=(args.method in [
                    "rag",
                    "react", "act", "react->cot-sc", "cot-sc->react"
                    ]),
                port=args.inf_vllm_port,
            )
        case _:
            model_kwargs = dict(
                model_path=args.model_path,
            )
    return model_kwargs


def get_agent_kwargs(args: argparse.Namespace) -> dict:
    match args.method:
        case "zeroshot":
            agent_kwargs = dict()
        case "fewshot":
            agent_kwargs = dict(
                fewshot_examples=FEWSHOT_EXAMPLES,
            )
        case "zeroshot-sc":
            agent_kwargs = dict(
                num_votes=args.sc_num_votes,
                sep=constants.answer_sep,
            )
        case "fewshot-sc":
            agent_kwargs = dict(
                num_votes=args.sc_num_votes,
                sep=constants.answer_sep,
                fewshot_examples=FEWSHOT_EXAMPLES,
            )

        case "cot":
            agent_kwargs = dict(
                cot_examples=COT_EXAMPLES
            )
        case "cot-sc":
            agent_kwargs = dict(
                cot_examples=COT_EXAMPLES,
                num_votes=args.sc_num_votes,
                sep=constants.answer_sep,
            )
        case "rag":
            agent_kwargs = dict(
                embedding="together", #args.embedding
                vector_store="faiss", #args.vector_store
                embedding_port=args.inf_embedding_port,
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
                cotsc_inf_temperature=constants.inf_temperature_hi, # react uses args.inf_temperature, cot-sc uses this hardcoded value
            )
        case "cot-sc->react":
            # Provide the second llm prompt (React) as an agent kwarg
            agent_kwargs = dict(
                cot_examples=COT_EXAMPLES,
                num_votes=args.sc_num_votes,
                sep=constants.answer_sep,
                cotsc_inf_temperature=constants.inf_temperature_hi, # react uses args.inf_temperature, cot-sc uses this hardcoded value
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
            logger.info(f"Loading dataset='{args.dataset}' :: {split=}")
            dataset = load_data(args.dataset, split)
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

            # If the model is a local LLM, we can run on all QA examples
            num_df_qa_pairs = len(df_qa_pairs)
            can_process_full_batch = (args.model_name in VLLMChat.SUPPORTED_LLM_NAMES) \
                and (args.method not in ["react", "act", "react->cot-sc", "cot-sc->react"])
            batch_size = num_df_qa_pairs if can_process_full_batch else args.batch_size
            for batch_number in range(1, math.ceil(num_df_qa_pairs/batch_size) + 1): #range(1, 2):
                run_name = (
                    f"split={split}" \
                    + f"__model_name={args.model_name.replace('/', '--')}" \
                    + f"__bs={batch_size}" \
                    + f"__bn={batch_number}" \
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
                logger.info(f"Getting predictions for questions [{batch_start_idx}, {batch_end_idx}) out of {num_df_qa_pairs}")
                batch_df_qa_pairs = df_qa_pairs.iloc[batch_start_idx:batch_end_idx]

                # Run the method and get final responses for the batch
                # In zeroshot, fewshot, the LLM responds with the final answer in 1 turn only,
                # so they support batch async inference
                agent_interactions = None
                match args.method:
                    case "zeroshot" | "zeroshot-sc" | "fewshot" | "fewshot-sc" | "rag":
                        questions: list[str] = batch_df_qa_pairs["question"].tolist()
                        inf_gen_config = default_inf_gen_config.model_copy(update=dict(seed=seed), deep=True)
                        responses: list[LLMChatResponse] = await agent.batch_run(llm_chat, questions, inf_gen_config)
                        # NOTE: the agent interactions are just single Conversation objects containing the prompt
                        # for the self-consistency methods, we save the Conversation object from the last iteration
                        agent_interactions: list[Conversation] = agent.agent_interactions
                    case "cot" | "cot-sc":
                        questions: list[str] = batch_df_qa_pairs["question"].tolist()
                        inf_gen_config = default_inf_gen_config.model_copy(update=dict(seed=seed), deep=True)
                        responses: list[LLMChatResponse] = await agent.batch_run(llm_chat, questions, inf_gen_config)
                        agent_interactions: list[Conversation] = agent.agent_interactions
                    # case "RAG":
                    #     raise NotImplementedError("RAG evaluation is not supported yet.")
                    case "react" | "act" | "react->cot-sc" | "cot-sc->react":
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
                    interactions=agent_interactions if not args.ignore_agent_interactions else [],
                )


def split_prolog_query(query: str) -> tuple[list[str], str | None]:
    """Split a compound Prolog query into individual queries and get final variable.
    
    Args:
        query: A Prolog query string like "?- hobby(X, 'bus spotting'), father(X, Y)."
        
    Returns:
        Tuple of (list of query strings, final variable letter or None)
        Example: (["hobby(X, 'bus spotting')", "father(X, Y)"], "Y")
    """
    
    # First clean up the full query
    query = query.strip()
    if query.startswith('?-'):
        query = query[2:].strip()
    if query.endswith('.'):
        query = query[:-1].strip()
    
    # Split on comma but respect parentheses and quotes
    queries = []
    current = []
    paren_count = 0
    in_quotes = False
    
    for char in query:
        if char == "'" and not in_quotes:
            in_quotes = True
            current.append(char)
        elif char == "'" and in_quotes:
            in_quotes = False
            current.append(char)
        elif char == '(' and not in_quotes:
            paren_count += 1
            current.append(char)
        elif char == ')' and not in_quotes:
            paren_count -= 1
            current.append(char)
        elif char == ',' and paren_count == 0 and not in_quotes:
            queries.append(''.join(current).strip())
            current = []
        else:
            current.append(char)
    
    if current:
        queries.append(''.join(current).strip())
    
    # Get final variable from last predicate
    final_variable = None
    if queries:
        last_pred = queries[-1]
        variables = [c for c in last_pred if c.isupper()]
        if variables:
            final_variable = variables[-1]
    
    return queries, final_variable


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
    
    # Get the absolute path to facts.pl
    facts_path = Path(__file__).parent.parent / "phantom_eval" / "facts.pl"
    logger.info(f"Looking for facts.pl at: {facts_path.absolute()}")
    if not facts_path.exists():
        raise FileNotFoundError(f"Could not find facts.pl at {facts_path.absolute()}")
    
    db = Database()
    db.from_disk(str(facts_path))
    for i, qa_sample in enumerate(batch_df_qa_pairs.itertuples()):
        uid = qa_sample.id
        
        # Split the query and execute each part
        query_results = []
        pred_query = responses[i].pred
        sub_queries, target_variable = split_prolog_query(pred_query)
        
        # Build the compound query incrementally
        compound_query = ""
        variable_bindings = {}
        
        for j, sub_query in enumerate(sub_queries):
            try:
                # Add this sub_query to compound query
                if compound_query:
                    compound_query += f", {sub_query}"
                else:
                    compound_query = sub_query
                
                # Execute the compound query up to this point
                result = db.query(compound_query)
                
                # Store result and variable bindings
                query_results.append({
                    'query': compound_query,
                    'sub_query_added': sub_query,
                    'result': result,
                    'variables': variable_bindings.copy()
                })
                
                # Update variable bindings from result
                if result:
                    for binding in result:
                        variable_bindings.update(binding)
                
            except Exception as e:
                logger.error(f"Query failed: {compound_query}")
                logger.error(f"Error: {str(e)}")
                query_results.append({
                    'query': compound_query,
                    'sub_query_added': sub_query,
                    'error': str(e),
                    'variables': variable_bindings.copy()
                })
                break  # Stop if any part fails
        
        # Use the final result for the prediction
        final_result = query_results[-1].get('result') if query_results else None
        
        # Get final value for target variable
        final_value = None
        if final_result and target_variable:
            for binding in final_result:
                if target_variable in binding:
                    final_value = binding[target_variable]
                    break
        
        preds[uid] = {
            "true": qa_sample.answer,
            "pred": final_value,
            "prolog_query": responses[i].pred,
            "prolog_bindings": final_result,
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
        
    accuracy = 0
    for pred in preds.values():
        if pred["true"] == [pred["pred"]]:
            accuracy += 1
    print(f"Accuracy: {accuracy / len(preds)} when evaluating {len(preds)} samples")


if __name__ == "__main__":
    parser = get_parser()
    args = parser.parse_args()
    setup_logging(args.log_level)

    # NOTE: asyncio.run should only be called once in a single Python instance.
    # Thus, any high-level function containing awaits in its implementation 
    # must be marked with the `async` keyword in the function definition.
    # See also: https://proxiesapi.com/articles/how-many-times-should-asyncio-run-be-called-python
    asyncio.run(main(args))
