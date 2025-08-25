"""
Training script for the GRPO model using Zeroshot or CoT prompt from PhantomEval.

Usage:
```bash
./scripts/train_grpo.sh recipes/qwen2.5-0.5b-instruct/grpo/config_base.yaml \
    --prompt_method cot \
    --output_dir /path/to/output_dir/
```
"""
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

import torch
from datasets import Dataset, concatenate_datasets
from peft import get_peft_model, prepare_model_for_kbit_training
from phantom_eval.agents.common import get_all_evidence
from phantom_eval.agents.cot import CoTAgent
from phantom_eval.constants import answer_sep
from phantom_eval.prompts import COT_EXAMPLES, CoTLLMPrompt, ZeroshotLLMPrompt
from phantom_eval.score import exact_match, f1, precision, recall
from phantom_eval.utils import load_data, setup_logging
from transformers import AutoModelForCausalLM, AutoTokenizer, set_seed
from transformers.trainer_utils import get_last_checkpoint
from trl import (
    GRPOTrainer,
    ModelConfig,
    ScriptArguments,
    TrlParser,
    get_peft_config,
    get_quantization_config,
)

from configs import GRPOConfig

logger = logging.getLogger(__name__)


############################################
# REWARD FUNCTIONS
############################################
def format_pred(pred: str, prompt_method: str) -> str:
    match prompt_method:
        case "zeroshot":
            return pred
        case "cot":
            try:
                return CoTAgent.parse_answer(pred)
            except ValueError:
                return ""
        case _:
            raise ValueError(f"Invalid {prompt_method=}")


def reward_exact_match(
    completions: list[list[dict[str, str]]], answer: list[list[str]], prompt_method: list[str], **kwargs
) -> list[float]:
    """
    Args:
        completions (shape (batch, len of convo)): Batch of completions,
            where each is a conversation (i.e. a list of dicts).
        answer: (shape (batch, # answers)): The true answers for the prompts.
        prompt_method: (shape (batch,)): The prompt method used for each sample.
    """
    # Format the model output text based on the prompting format
    preds = [
        format_pred(completion[0]["content"], method)
        for completion, method in zip(completions, prompt_method)
    ]
    return [float(exact_match(pred, answer_sep.join(a))) for pred, a in zip(preds, answer)]


def reward_precision(
    completions: list[list[dict[str, str]]], answer: list[list[str]], prompt_method: list[str], **kwargs
) -> list[float]:
    """
    Args:
        completions (shape (batch, len of convo)): Batch of completions,
            where each is a conversation (i.e. a list of dicts).
        answer: (shape (batch, # answers)): The true answers for the prompts.
        prompt_method: (shape (batch,)): The prompt method used for each sample.
    """
    # Format the model output text based on the prompting format
    preds = [
        format_pred(completion[0]["content"], method)
        for completion, method in zip(completions, prompt_method)
    ]
    return [float(precision(pred, answer_sep.join(a))) for pred, a in zip(preds, answer)]


def reward_recall(
    completions: list[list[dict[str, str]]], answer: list[list[str]], prompt_method: list[str], **kwargs
) -> list[float]:
    """
    Args:
        completions (shape (batch, len of convo)): Batch of completions,
            where each is a conversation (i.e. a list of dicts).
        answer: (shape (batch, # answers)): The true answers for the prompts.
        prompt_method: (shape (batch,)): The prompt method used for each sample.
    """
    # Format the model output text based on the prompting format
    preds = [
        format_pred(completion[0]["content"], method)
        for completion, method in zip(completions, prompt_method)
    ]
    return [float(recall(pred, answer_sep.join(a))) for pred, a in zip(preds, answer)]


def reward_f1(
    completions: list[list[dict[str, str]]], answer: list[list[str]], prompt_method: list[str], **kwargs
) -> list[float]:
    """
    Args:
        completions (shape (batch, len of convo)): Batch of completions,
            where each is a conversation (i.e. a list of dicts).
        answer: (shape (batch, # answers)): The true answers for the prompts.
        prompt_method: (shape (batch,)): The prompt method used for each sample.
    """
    # Format the model output text based on the prompting format
    preds = [
        format_pred(completion[0]["content"], method)
        for completion, method in zip(completions, prompt_method)
    ]
    return [float(f1(pred, answer_sep.join(a))) for pred, a in zip(preds, answer)]


def get_reward_func(reward_type_name: str) -> callable:
    match reward_type_name:
        case "exact_match":
            return reward_exact_match
        case "precision":
            return reward_precision
        case "recall":
            return reward_recall
        case "f1":
            return reward_f1
        case _:
            raise ValueError(f"Invalid {reward_type_name=}")


############################################
# SCRIPT ARGUMENTS
############################################
@dataclass
class GRPOScriptArguments(ScriptArguments):
    # Train dataset arguments
    dataset_name: str = "kilian-group/phantom-wiki-v1"
    split_list: list[str] = field(
        default_factory=lambda: ["depth_20_size_50_seed_1", "depth_20_size_50_seed_2"]
    )
    from_local: bool = False
    # Eval dataset arguments
    eval_dataset_name: str = "kilian-group/phantom-wiki-v1"
    eval_split_list: str = field(default_factory=lambda: ["depth_20_size_50_seed_3"])
    eval_from_local: bool = False
    # Script arguments
    reward_func_names: list[str] = field(default_factory=lambda: ["f1"])
    prompt_method: Literal["zeroshot", "cot"] = "zeroshot"


def get_checkpoint(training_args: GRPOConfig):
    last_checkpoint = None
    if os.path.isdir(training_args.output_dir):
        last_checkpoint = get_last_checkpoint(training_args.output_dir)
    return last_checkpoint


def get_prompt_for_sample(sample: dict[str, Any], evidence: str, prompt_method: str) -> list[dict[str, str]]:
    """
    Get the prompt for a sample, depending on the prompt method.

    Args:
        sample (dict[str, Any]): A sample from the dataset, with key "question".
        evidence (str): The evidence text to include in the prompt.
        prompt_method (str): Either "zeroshot" or "cot".

    Returns:
        list[dict[str, str]]: A list of messages for the conversational-style prompt.
            Each message is a dict with keys "role" and "content".
    """
    match prompt_method:
        case "zeroshot":
            llm_prompt = ZeroshotLLMPrompt()
            prompt = [
                {
                    "role": "user",
                    "content": llm_prompt.get_prompt().format(evidence=evidence, question=sample["question"]),
                },
            ]
            return prompt

        case "cot":
            llm_prompt = CoTLLMPrompt()
            return [
                {
                    "role": "user",
                    "content": llm_prompt.get_prompt().format(
                        evidence=evidence, examples=COT_EXAMPLES, question=sample["question"]
                    ),
                },
            ]
        case _:
            raise ValueError(f"Invalid {prompt_method=}")


def get_pw_dataset(dataset_name: str, split_list: list[str], from_local: bool) -> Dataset:
    all_datasets: list[Dataset] = []
    for split_name in split_list:
        dataset: dict[str, Dataset] = load_data(dataset_name, split=split_name, from_local=from_local)
        text_corpus: Dataset = dataset["text"]
        qa_pairs: Dataset = dataset["qa_pairs"]
        evidence: str = get_all_evidence(text_corpus)

        dataset: Dataset = qa_pairs.map(
            lambda sample: {
                "prompt": get_prompt_for_sample(sample, evidence, script_args.prompt_method),
                "answer": sample["answer"],  # sample['answer'] is a list of strings
                "prompt_method": script_args.prompt_method,
            }
        )
        all_datasets.append(dataset)
    return concatenate_datasets(all_datasets)


def train_grpo(script_args: GRPOScriptArguments, training_args: GRPOConfig, model_args: ModelConfig) -> None:
    """Training script for the GRPO model using Zeroshot prompt from PhantomEval.

    Args:
        script_args: Script arguments.
        training_args: Training arguments.
        model_args: Model arguments.
    """
    # Get train dataset
    train_dataset = get_pw_dataset(script_args.dataset_name, script_args.split_list, script_args.from_local)
    logger.info(
        f"*** Loaded train dataset {script_args.dataset_name}::{script_args.split_list} "
        f"with {len(train_dataset)} samples."
    )

    # Get eval dataset
    eval_dataset = get_pw_dataset(
        script_args.eval_dataset_name, script_args.eval_split_list, script_args.eval_from_local
    )
    logger.info(
        f"*** Loaded eval dataset {script_args.eval_dataset_name}::{script_args.eval_split_list} "
        f"with {len(eval_dataset)} samples."
    )

    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        model_args.model_name_or_path, trust_remote_code=model_args.trust_remote_code, use_fast=True
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    reward_funcs: list[callable] = [
        get_reward_func(reward_func_name) for reward_func_name in script_args.reward_func_names
    ]
    logger.info(f"*** Selected reward functions: {script_args.reward_func_names}")

    logger.info("*** Initializing model kwargs ***")
    torch_dtype = (
        model_args.torch_dtype
        if model_args.torch_dtype in ["auto", None]
        else getattr(torch, model_args.torch_dtype)
    )
    model_kwargs = dict(
        revision=model_args.model_revision,
        trust_remote_code=model_args.trust_remote_code,
        attn_implementation=model_args.attn_implementation,
        torch_dtype=torch_dtype,
        use_cache=False if training_args.gradient_checkpointing else True,
        quantization_config=get_quantization_config(model_args) if model_args.use_peft else None,
    )
    logger.info(f"*** Model kwargs: {model_kwargs} ***")
    # NOTE: GRPOTrainer does not prepare model for kbit training,
    # so we do it outside of the trainer manually
    # Reference: https://huggingface.co/docs/peft/en/developer_guides/quantization
    model = AutoModelForCausalLM.from_pretrained(
        model_args.model_name_or_path,
        **model_kwargs,
    )
    if model_kwargs["quantization_config"] is not None:
        logger.info("*** Preparing model for kbit training ***")
        model = prepare_model_for_kbit_training(model)
    if model_args.use_peft:
        logger.info("*** Initializing PEFT model ***")
        lora_config = get_peft_config(model_args)
        model = get_peft_model(model, lora_config)

    # Instantiate the trainer
    trainer = GRPOTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        processing_class=tokenizer,
        reward_funcs=reward_funcs,
    )
    logger.info(f"*** Instantiated GRPO trainer for model {model_args.model_name_or_path}")

    # Training loop
    # Check for last checkpoint
    last_checkpoint = get_checkpoint(training_args)
    if last_checkpoint is not None and training_args.resume_from_checkpoint is None:
        logger.info(f"Checkpoint detected, resuming training at {last_checkpoint}.")
    # Training loop
    logger.info(
        f"*** Starting training {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} "
        f"for {training_args.num_train_epochs} epochs"
    )
    train_result = trainer.train(resume_from_checkpoint=last_checkpoint)
    # Log and save metrics
    metrics = train_result.metrics
    metrics["train_samples"] = len(train_dataset)
    trainer.log_metrics("train", metrics)
    trainer.save_metrics("train", metrics)
    trainer.save_state()

    logger.info("*** Training complete")

    ##################################
    # Save model and create model card
    ##################################

    logger.info("*** Save model")
    trainer.model.config.use_cache = True
    trainer.save_model(training_args.output_dir)
    logger.info(f"*** Model saved to {training_args.output_dir}")
    training_args.distributed_state.wait_for_everyone()  # wait for all processes to load

    tokenizer.save_pretrained(training_args.output_dir)
    logger.info(f"*** Tokenizer saved to {training_args.output_dir}")


if __name__ == "__main__":
    parser = TrlParser((GRPOScriptArguments, GRPOConfig, ModelConfig))
    script_args, training_args, model_args = parser.parse_args_and_config()
    setup_logging(training_args.log_level.upper())
    set_seed(training_args.seed)

    train_grpo(script_args, training_args, model_args)
