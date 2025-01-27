# Single column figures
TICK_FONT_SIZE = 8
LABEL_FONT_SIZE = 10

MODEL_ALIASES = {
    'google/gemma-2-27b-it': "Gemma-2-27B",
    'google/gemma-2-9b-it': "Gemma-2-9B",
    'google/gemma-2-2b-it': "Gemma-2-2B",
    'meta-llama/llama-3.3-70b-instruct': "Llama-3.3-70B",
    'meta-llama/llama-3.1-70b-instruct': "Llama-3.1-70B",
    'meta-llama/llama-3.1-8b-instruct': "Llama-3.1-8B",
    'meta-llama/llama-3.2-3b-instruct': "Llama-3.2-3B",
    'meta-llama/llama-3.2-1b-instruct': "Llama-3.2-1B",
    'microsoft/phi-3.5-moe-instruct': "Phi-3.5-MoE",
    'microsoft/phi-3.5-mini-instruct': "Phi-3.5-Mini",
    'mistralai/mistral-7b-instruct-v0.3': "Mistral-7B",
    'gemini-1.5-flash-8b-001': "Gemini-1.5-Flash-8B",
    'gemini-1.5-flash-002': "Gemini-1.5-Flash",
    'gemini-2.0-flash-exp': "Gemini-2.0-Flash",
    'gpt-4o-mini-2024-07-18': "GPT-4o-Mini",
    'gpt-4o-2024-11-20': 'GPT-4o',
    'deepseek-ai/deepseek-r1-distill-qwen-32b': 'DeepSeek-R1-32B',
}

DEFAULT_METHOD_LIST = [
    "zeroshot", 
    "cot", 
    "zeroshot-retriever", 
    "cot-retriever", 
    "react", 
    "reasoning"
]
DEFAULT_MODEL_LIST = [ 
    "gemini-1.5-flash-002", 
    "meta-llama/llama-3.3-70b-instruct", 
    "deepseek-ai/deepseek-r1-distill-qwen-32b"
]