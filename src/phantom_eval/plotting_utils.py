import matplotlib.pyplot as plt

# utils for plotting
plt.rcParams.update(
    {
        "font.family": "serif",
        "mathtext.fontset": "stix",
        "axes.spines.top": False,
        "axes.spines.right": False,
    }
)
COLORS = {
    "google/gemma-3-1b-it": "tab:blue",
    "google/gemma-2-27b-it": "tab:blue",
    "google/gemma-2-9b-it": "tab:blue",
    "google/gemma-2-2b-it": "tab:blue",
    "meta-llama/llama-3.3-70b-instruct": "tab:orange",
    "meta-llama/llama-3.1-70b-instruct": "tab:orange",
    "meta-llama/llama-3.1-8b-instruct": "tab:orange",
    "meta-llama/llama-3.2-3b-instruct": "tab:orange",
    "meta-llama/llama-3.2-1b-instruct": "tab:orange",
    "microsoft/phi-3.5-moe-instruct": "tab:green",
    "microsoft/phi-3.5-mini-instruct": "tab:green",
    "mistralai/mistral-7b-instruct-v0.3": "tab:red",
    "gemini-1.5-flash-002": "tab:purple",
    "gemini-1.5-flash-8b-001": "tab:purple",
    "gemini-2.0-flash-exp": "tab:purple",
    "gpt-4o-mini-2024-07-18": "tab:brown",
    "gpt-4o-2024-11-20": "tab:brown",
    "deepseek-ai/deepseek-r1-distill-qwen-32b": "tab:green",
    "deepseek-ai/deepseek-r1-distill-qwen-7b": "tab:green",
    "deepseek-ai/deepseek-r1-distill-qwen-1.5b": "tab:green",
    "qwen/qwen2.5-32b-instruct": "tab:red",
    "qwen/qwen2.5-7b-instruct": "tab:red",
    "qwen/qwen2.5-3b-instruct": "tab:red",
    "qwen/qwen2.5-1.5b-instruct": "tab:red",
    "qwen/qwen2.5-0.5b-instruct": "#ff9999",  # NOTE: light red
}
LINESTYLES = {
    "google/gemma-3-1b-it": "dotted",
    "google/gemma-2-27b-it": "-",
    "google/gemma-2-9b-it": "--",
    "google/gemma-2-2b-it": "dotted",
    "meta-llama/llama-3.3-70b-instruct": "dashdot",
    "meta-llama/llama-3.1-70b-instruct": "-",
    "meta-llama/llama-3.1-8b-instruct": "--",
    "meta-llama/llama-3.2-3b-instruct": "dotted",
    "meta-llama/llama-3.2-1b-instruct": (10, (1, 10)),  # loosely dotted
    "microsoft/phi-3.5-moe-instruct": "-",
    "microsoft/phi-3.5-mini-instruct": "--",
    "mistralai/mistral-7b-instruct-v0.3": "-",
    "gemini-2.0-flash-exp": "-",
    "gemini-1.5-flash-002": "--",
    "gemini-1.5-flash-8b-001": "dotted",
    "gpt-4o-mini-2024-07-18": "-",
    "gpt-4o-2024-11-20": "--",
    "deepseek-ai/deepseek-r1-distill-qwen-32b": "-",
    "deepseek-ai/deepseek-r1-distill-qwen-7b": "-",
    "deepseek-ai/deepseek-r1-distill-qwen-1.5b": "-",
    "qwen/qwen2.5-32b-instruct": "-",
    "qwen/qwen2.5-7b-instruct": "--",
    "qwen/qwen2.5-3b-instruct": "dotted",
    "qwen/qwen2.5-1.5b-instruct": (10, (1, 10)),
    "qwen/qwen2.5-0.5b-instruct": (10, (1, 10)),
}
METHOD_LINESTYLES = {
    "zeroshot": "--",
    "cot": "-",
    "zeroshot-rag": "--",
    "cot-rag": "-",
    "act": "--",
    "react": "-",
    "selfask": "dotted",
    "ircot": "dashdot",
    "sft": "dotted",
    "grpo": "dashdot",
}
HATCHSTYLES = {
    "google/gemma-2-27b-it": "/",
    "google/gemma-2-9b-it": "\\",
    "google/gemma-2-2b-it": "|",
    "meta-llama/llama-3.3-70b-instruct": "-",
    "meta-llama/llama-3.1-70b-instruct": "+",
    "meta-llama/llama-3.1-8b-instruct": "x",
    "meta-llama/llama-3.2-3b-instruct": "o",
    "meta-llama/llama-3.2-1b-instruct": "O",
    "microsoft/phi-3.5-moe-instruct": ".",
    "microsoft/phi-3.5-mini-instruct": "*",
    "mistralai/mistral-7b-instruct-v0.3": "//",
    "gemini-2.0-flash-exp": "\\\\",
    "gemini-1.5-flash-002": "||",
    "gemini-1.5-flash-8b-001": "--",
    "gpt-4o-mini-2024-07-18": "++",
    "gpt-4o-2024-11-20": "xx",
    "deepseek-ai/deepseek-r1-distill-qwen-32b": "++",
    "deepseek-ai/deepseek-r1-distill-qwen-7b": "++",
    "deepseek-ai/deepseek-r1-distill-qwen-1.5b": "++",
    "qwen/qwen2.5-32b-instruct": "/",
    "qwen/qwen2.5-7b-instruct": "\\",
    "qwen/qwen2.5-3b-instruct": "|",
    "qwen/qwen2.5-1.5b-instruct": "|",
    "qwen/qwen2.5-0.5b-instruct": "|",
}
# https://matplotlib.org/stable/gallery/lines_bars_and_markers/marker_reference.html#filled-markers
MARKERS = {
    "zeroshot": "^",  # upward triangle
    "cot": "s",  # square
    "zeroshot-rag": "^",  # upward triangle
    "cot-rag": "s",  # square
    "act": "+",  # plus
    "react": "P",  # bold plus
}

# Single column figures
TICK_FONT_SIZE = 6
MINOR_TICK_FONT_SIZE = 3
LABEL_FONT_SIZE = 10
LEGEND_FONT_SIZE = 7
MARKER_ALPHA = 1
MARKER_SIZE = 3
LINE_ALPHA = 0.75
OUTWARD = 4

MODEL_ALIASES = {
    "google/gemma-3-1b-it": "Gemma-3-1B",
    "google/gemma-2-27b-it": "Gemma-2-27B",
    "google/gemma-2-9b-it": "Gemma-2-9B",
    "google/gemma-2-2b-it": "Gemma-2-2B",
    "meta-llama/llama-3.3-70b-instruct": "Llama-3.3-70B",
    "meta-llama/llama-3.1-70b-instruct": "Llama-3.1-70B",
    "meta-llama/llama-3.1-8b-instruct": "Llama-3.1-8B",
    "meta-llama/llama-3.2-3b-instruct": "Llama-3.2-3B",
    "meta-llama/llama-3.2-1b-instruct": "Llama-3.2-1B",
    "microsoft/phi-3.5-moe-instruct": "Phi-3.5-MoE",
    "microsoft/phi-3.5-mini-instruct": "Phi-3.5-Mini",
    "mistralai/mistral-7b-instruct-v0.3": "Mistral-7B",
    "gemini-1.5-flash-8b-001": "Gemini-1.5-Flash-8B",
    "gemini-1.5-flash-002": "Gemini-1.5-Flash",
    "gemini-2.0-flash-exp": "Gemini-2.0-Flash",
    "gpt-4o-mini-2024-07-18": "GPT-4o-Mini",
    "gpt-4o-2024-11-20": "GPT-4o",
    "deepseek-ai/deepseek-r1-distill-qwen-32b": "DeepSeek-R1-32B",
    "deepseek-ai/deepseek-r1-distill-qwen-7b": "DeepSeek-R1-7B",
    "deepseek-ai/deepseek-r1-distill-qwen-1.5b": "DeepSeek-R1-1.5B",
    "qwen/qwen2.5-32b-instruct": "Qwen2.5-32B",
    "qwen/qwen2.5-7b-instruct": "Qwen2.5-7B",
    "qwen/qwen2.5-3b-instruct": "Qwen2.5-3B",
    "qwen/qwen2.5-1.5b-instruct": "Qwen2.5-1.5B",
    "qwen/qwen2.5-0.5b-instruct": "Qwen2.5-0.5B",
}
METHOD_LATEX_ALIASES = {
    "zeroshot": "\\textsc{Zeroshot}",
    "cot": "\\textsc{CoT}",
    "zeroshot-rag": "\\textsc{Zeroshot-RAG}",
    "cot-rag": "\\textsc{CoT-RAG}",
    "act": "\\textsc{Act}",
    "react": "\\textsc{ReAct}",
    "selfask": "\\textsc{Self-Ask}",
    "ircot": "\\textsc{IRCoT}",
    "sft": "\\textsc{SFT}",
    "grpo": "\\textsc{GRPO}",
}
METHOD_ALIASES = {
    "zeroshot": "ZeroShot",
    "cot": "CoT",
    "zeroshot-rag": "ZeroShot-RAG",
    "cot-rag": "CoT-RAG",
    "act": "Act",
    "react": "ReAct",
    "selfask": "Self-Ask",
    "ircot": "IRCoT",
    "sft": "SFT",
    "grpo": "GRPO",
}
INCONTEXT_METHODS = [
    "zeroshot",
    "cot",
]
RAG_METHODS = [
    "zeroshot-rag",
    "cot-rag",
    "selfask",
    "ircot",
]
AGENTIC_METHODS = [
    "react",
]
DEFAULT_METHOD_LIST = [
    *INCONTEXT_METHODS,
    *RAG_METHODS,
    *AGENTIC_METHODS,
]
DEFAULT_MODEL_LIST = [
    "deepseek-ai/deepseek-r1-distill-qwen-32b",
    "gemini-1.5-flash-002",
    "gpt-4o-2024-11-20",
    "meta-llama/llama-3.3-70b-instruct",
]

import numpy as np

DEC = np.arange(1, 11)
