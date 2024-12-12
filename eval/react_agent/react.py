"""
Script for getting predictions for react agent.
"""

import argparse
import json
# import logging
import os
from pathlib import Path
from typing import Any

import pandas as pd

from agents import ReactAgent
import llm
import prompts
from phantom_eval.utils import load_data


def main(args: argparse.Namespace) -> None:
    print("* Loading dataset")
    dataset = load_data(args.split)
    df_qa_pairs = pd.DataFrame(dataset["qa_pairs"])
    df_text = pd.DataFrame(dataset["text"])

    # TODO Filter one type of question
    df_qa_pairs = df_qa_pairs.loc[df_qa_pairs["type"] == 1, :]
    df_qa_pairs = df_qa_pairs[:args.num_samples]
    df_qa_pairs = df_qa_pairs.reset_index(drop=True)

    print("* Loading LLM")
    model_kwargs = dict(
        model_path=args.model_path,
        max_tokens=args.sampling_max_tokens,
        temperature=args.sampling_temperature,
        seed=args.sampling_seed,
        max_retries=args.sampling_max_retries,
        wait_seconds=args.sampling_wait_seconds,
    )
    llm_chat = llm.get_llm(args.model_name, model_kwargs=model_kwargs)
    llm_prompts = prompts.get_llm_prompt(args.model_name)

    # Construct react agent for each sample in the QA dataset
    print(f"Constructing ReAct agent for {len(df_qa_pairs)} samples")
    agents: list[ReactAgent] = []
    for i, sample in enumerate(df_qa_pairs.itertuples()):
        agent = ReactAgent(
            sample.question,
            sample.answer,
            agent_prompt=llm_prompts.get_react_prompt(),
            max_steps=args.react_max_steps,
            text_corpus=df_text,
            react_examples=prompts.REACT_EXAMPLES6,
        )
        agents.append(agent)

    # Run the agents and log the final answers
    # TODO save after each agent run
    print(f"Running ReAct agent for {len(agents)} samples")
    answers: list[dict[str, Any]] = []
    for agent in agents:
        # blue(agent.question)
        agent.run(llm_chat)
        # TODO Add usage dump
        answers.append({
            "pred": agent.answer,
            "interaction": agent._build_agent_prompt(),
        })
    
    run_name = f"split={args.split}__model_name={args.model_name.replace('/', '--')}"
    save_preds(run_name, args, df_qa_pairs, answers)


def save_preds(run_name: str, args: argparse.Namespace, df_qa_pairs: pd.DataFrame, answers: list[dict, str, Any]) -> None:
    preds = {}
    batch_size = len(df_qa_pairs)
    for i in range(batch_size):
        uid = df_qa_pairs.at[i, "id"]
        preds[uid] = {
            "true" : df_qa_pairs.at[i, "answer"],
            "pred" : answers[i]["pred"],
            "interaction": answers[i]["interaction"],
            "metadata": {
                "model": args.model_name,
                "split": args.split,
                "batch_size": batch_size,
                "batch_number": 1,
                "type": int(df_qa_pairs.at[i, "type"]),
            },
            "sampling_params": {
                "max_tokens": args.sampling_max_tokens,
                "temperature": args.sampling_temperature,
                "seed": args.sampling_seed,
                "max_retries": args.sampling_max_retries,
                "wait_seconds": args.sampling_wait_seconds
            },
            # "usage": responses[i]["usage"],
        }

    pred_path = Path(args.output_dir) / "react" / "preds" / f"{run_name}.json"
    pred_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Saving predictions to {pred_path}")
    with open(pred_path, "w") as f:
        json.dump(preds, f, indent=4)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    
    # Model arguments
    parser.add_argument("--model_name", type=str, default="together:meta-llama/Llama-Vision-Free", choices=llm.SUPPORTED_LLM_NAMES)
    parser.add_argument("--model_path", type=str, default=None, help="Path to the model")
    parser.add_argument("--sampling_max_tokens", type=int, default=4096, help="Maximum number of tokens to generate")
    parser.add_argument("--sampling_temperature", type=float, default=0.0, help="Temperature for sampling")
    parser.add_argument("--sampling_seed", type=int, default=0, help="Seed for sampling")
    parser.add_argument("--sampling_max_retries", type=int, default=3, help="Number of tries to get response")
    parser.add_argument("--sampling_wait_seconds", type=int, default=2, help="Seconds to wait between tries")

    # Dataset arguments
    parser.add_argument("--split", type=str, default="depth_6_size_26_seed_1")
    parser.add_argument("--num_samples", type=int, default=5, help="Number of dataset samples to evaluate")

    # React Agent arguments
    parser.add_argument("--react_max_steps", type=int, default=6, help="Number of steps to run the agent")

    # Logging arguments
    parser.add_argument("--output_dir", type=str, default="out", help="Output directory for logs")

    args, unknown = parser.parse_known_args()

    main(args)