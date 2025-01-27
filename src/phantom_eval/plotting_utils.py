# Single column figures
TICK_FONT_SIZE = 8
LABEL_FONT_SIZE = 10
LEGEND_FONT_SIZE = 8

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
METHOD_ALIASES = {
    'zeroshot': 'Zeroshot',
    'cot': 'CoT',
    'zeroshot-rag': 'Zeroshot-RAG',
    'cot-rag': 'CoT-RAG',
    'react': 'ReAct',
    'reasoning': 'Reasoning'
}
DEFAULT_METHOD_LIST = [
    "zeroshot", 
    "cot", 
    "zeroshot-rag", 
    "cot-rag", 
    "react", 
    "reasoning"
]
SIMPLE_METHODS = [
    "zeroshot",
    "cot",
    "reasoning",
]
RAG_METHODS = [
    "zeroshot-rag",
    "cot-rag",
]
AGENTIC_METHODS = [
    # "act",
    "react",
]
DEFAULT_MODEL_LIST = [ 
    "deepseek-ai/deepseek-r1-distill-qwen-32b",
    "gemini-1.5-flash-002", 
    "gpt-4o-2024-11-20",
    "meta-llama/llama-3.3-70b-instruct", 
]