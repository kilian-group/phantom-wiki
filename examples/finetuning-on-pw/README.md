# Finetuning on PhantomWiki datasets

We finetune models on PhantomWiki-generated datasets with SFT and GRPO.

## Setup instructions

The finetuning scripts require libraries for training LLMs, e.g. `trl`,
and use `phantom-wiki` as a dependency.
Hence, we recommend creating a separate environment for finetuning experiments.

```bash
# Create new environment
conda create -n pw-finetuning python=3.12
conda activate pw-finetuning

# Install SWI-prolog. On linux:
conda install conda-forge::swi-prolog
# or on mac:
brew install swi-prolog

pip install -r requirements.txt
pip install flash-attn --no-build-isolation
```

> \[!NOTE\]
> The `flash-attn` dependency restricts the system requirements to Linux with CUDA/ROCm toolkit support.

## Generating PhantomWiki data for finetuning

There are 3\*3 evaluation splits on Huggingface at `"kilian-group/phantom-wiki-v1"`: `depth_20_size_{50,500,5000}_seed_{1,2,3}`.
We care about `depth_20_size_50_seed_{1,2,3}` as the bigger universe sizes do
not fit in 32K context length models.

We can finetune LLMs on 10 other seeds `depth_20_size_50_seed_{10,...,19}`, which we can generate using `phantom-wiki` with:

```bash
# Generating many datasets, except 1..3 that are used for evaluation
for seed in {10..50}; do ./scripts/generate-data.sh data/wiki-v1 $seed; done
```

> \[!NOTE\]
> If you see import errors due to sqlite3, reinstalling `libsqlite` with `conda install libsqlite --force-reinstall` can work.

## GRPO experiments

To full-finetune https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct model, we allocate a node of 4 A100s/H100s with 8 CPUs and 100GB RAM.
Then we run:

```bash
./scripts/train_grpo.sh recipes/qwen2.5-0.5b-instruct/grpo/config_base.yaml --prompt_method cot --output_dir /path/to/output_dir/
```

We also finetune https://huggingface.co/Qwen/Qwen2.5-3B-Instruct model with LoRA by running the following.
It saves LoRA adapter weights in the output directory, which can be evaluated via Huggingface and vLLM.

```bash
./scripts/train_grpo.sh recipes/qwen2.5-3b-instruct/grpo/config_lora.yaml --prompt_method cot --output_dir /path/to/output_dir/
```

## SFT experiments

PhantomWiki provides ground truth answers for each question, and hence we can Supervise FineTune LLMs on `(prompt=documents, output=answer list)` using the
`zeroshot` prompt template.
Again we allocate a node of 4 A100s/H100s with 8 CPUs and 100GB RAM, and run:

```bash
./scripts/train_sft_on_docs.sh recipes/qwen2.5-0.5b-instruct/sft/config_on_docs_base.yaml --output_dir /path/to/output_dir/
# LoRA on 3B model
./scripts/train_sft_on_docs.sh recipes/qwen2.5-3b-instruct/sft/config_on_docs_lora.yaml --output_dir /path/to/output_dir/
```

## Evaluating GRPO/SFT finetuned LLMs on PhantomWiki

Now, run phantom-eval on the saved checkpoints:

```bash
python -m phantom_eval \
	--method cot \
	--server vllm \
	--inf_vllm_offline \
	--model_name /path/to/model/checkpoint/ \
	--dataset kilian-group/phantom-wiki-v1 \
	--split_list depth_20_size_50_seed_1 depth_20_size_50_seed_2 depth_20_size_50_seed_3 \
	-od /path/to/output_for_preds/
```

PhantomEval also supports evaluating LoRA-finetuned checkpoints in the following way:

```bash
python -m phantom_eval \
	--method cot \
	--server vllm \
	--inf_vllm_online \
	--model_name Qwen/Qwen2.5-3B-Instruct \
	--inf_vllm_lora_path /path/to/model/checkpoint/ \
	--dataset kilian-group/phantom-wiki-v1 \
	--split_list depth_20_size_50_seed_1 depth_20_size_50_seed_2 depth_20_size_50_seed_3 \
	-od /path/to/output_for_preds/
```

> \[!NOTE\]
> If you get vllm errors due to tensor parallel size, it means that vllm is unable to distribute your checkpoint across the GPUs. In this case, you can use just 1 GPU to run evaluation:

```bash
CUDA_VISIBLE_DEVICES=0 python -m phantom_eval \
	--method cot \
	--server vllm \
	--inf_vllm_offline \
	--model_name /path/to/model/checkpoint/ \
	--dataset kilian-group/phantom-wiki-v1 \
	--split_list depth_20_size_50_seed_1 depth_20_size_50_seed_2 depth_20_size_50_seed_3 \
	-od /path/to/output_for_preds/ \
	--inf_vllm_tensor_parallel_size 1
```