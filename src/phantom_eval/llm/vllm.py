import asyncio
import logging
import uuid

import openai
from transformers import AutoTokenizer
from vllm import LLM, SamplingParams
from vllm.lora.request import LoRARequest

from phantom_eval._types import ContentTextMessage, Conversation, LLMChatResponse
from phantom_eval.gpu_utils import get_gpu_count
from phantom_eval.llm.common import CommonLLMChat, InferenceGenerationConfig

logger = logging.getLogger(__name__)


class VLLMChat(CommonLLMChat):
    def __init__(
        self,
        model_name: str,
        max_model_len: int | None = None,
        tensor_parallel_size: int | None = None,
        lora_path: str | None = None,
        use_api: bool = False,
        port: int = 8000,
        is_deepseek_r1_model: bool = False,
    ):
        """
        Args:
            max_model_len (int): Maximum model length for vLLM models.
                Defaults to None.
            tensor_parallel_size (int): Number of GPUs to use for tensor parallelism.
                Defaults to None (uses all available GPUs).
            lora_path (str): Path to the LoRA weights.
                Defaults to None.
            use_api (bool): Whether to use the vllm server or offline inference
                Defaults to False.
                NOTE: offline inference only works for batch_generate_response
                To maximize performance, set `use_api=False` when running Nshot and CoT agents
            port (int): Port number for the vllm server.
                Defaults to 8000.
            is_deepseek_r1_model (bool): Whether the model is a distilled deepseek r1 model.
                We add the stop token "<|end_of_sentence|>" for these models.
                If False, we add the stop token "<|eot_id|>".
                Defaults to False.
        """
        # NOTE: with vllm, we don't need to enforce rate limits. So we don't call self._update_rate_limits()
        # at the end __init__() either
        super().__init__(model_name, enforce_rate_limits=False)

        # Handle additional stop token for all distilled deepseek r1 models
        if is_deepseek_r1_model:
            self.ADDITIONAL_STOP = ["<｜end▁of▁sentence｜>"]
        else:
            self.ADDITIONAL_STOP = ["<|eot_id|>"]

        self.lora_path = lora_path
        self.use_api = use_api

        if self.use_api:
            logger.info("Using vLLM server for inference")
            try:
                BASE_URL = f"http://0.0.0.0:{port}/v1"
                API_KEY = "token-abc123"  # TODO: allow this to be specified by the user
                self.client = openai.OpenAI(
                    base_url=BASE_URL,
                    api_key=API_KEY,
                )
                self.async_client = openai.AsyncOpenAI(
                    base_url=BASE_URL,
                    api_key=API_KEY,
                )
            except openai.APIConnectionError as e:
                logger.error(
                    "Make sure to launch the vllm server using "
                    "vllm serve MODEL_NAME_OR_PATH --api-key token-abc123 --tensor_parallel_size NUM_GPUS"
                )
                raise e
        else:
            logger.info("Using vLLM batched offline inference")
            # vLLM configs
            self.max_model_len = max_model_len
            if tensor_parallel_size is None:
                # NOTE: the reason why we can't use torch.cuda.device_count() is because of some weird bug
                # between torch and vllm,
                # where we can't call `import torch` before instantiating the LLM object
                self.tensor_parallel_size = get_gpu_count()
            else:
                self.tensor_parallel_size = tensor_parallel_size
            # instead of initializing a client, we initialize the LLM object
            if self.lora_path is not None:
                logger.info(f"Using LoRA weights {self.lora_path} for inference")
            self.llm = LLM(
                model=self.model_name,
                max_model_len=self.max_model_len,
                tensor_parallel_size=self.tensor_parallel_size,
                enable_lora=self.lora_path is not None,
            )
            # get tokenizer for constructing prompt
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, trust_remote_code=True)

    def _convert_conv_to_api_format(self, conv: Conversation) -> list[dict]:
        formatted_messages = []
        for message in conv.messages:
            for content in message.content:
                match content:
                    case ContentTextMessage(text=text):
                        formatted_messages.append({"role": message.role, "content": text})
        return formatted_messages

    def _parse_api_output(
        self, response: object, inf_gen_config: InferenceGenerationConfig | None = None
    ) -> LLMChatResponse:
        """Parse the output of vllm server when using the OpenAI compatible server

        NOTE: we don't use inf_gen_config for parsing the output of the vllm server"""
        return LLMChatResponse(
            pred=response.choices[0].message.content,
            usage=response.usage.model_dump(),
        )

    def _parse_batch_vllm_output(self, response: object) -> LLMChatResponse:
        """Parse output of vllm offline inference when using batch offline inference"""
        return LLMChatResponse(
            pred=response.outputs[0].text,
            usage={
                "prompt_tokens": len(response.prompt_token_ids),
                "completion_tokens": len(response.outputs[0].token_ids),
                "total_tokens": len(response.prompt_token_ids) + len(response.outputs[0].token_ids),
                "cached_tokens": response.num_cached_tokens,
            },
        )

    def _call_api(
        self,
        messages_api_format: list[dict],
        inf_gen_config: InferenceGenerationConfig,
        use_async: bool = False,
    ) -> object:
        # NOTE: vllm implements an OpenAI compatible server
        # https://github.com/openai/openai-python
        assert self.use_api, "This function should not be called when using vllm batched offline inference"
        client = self.async_client if use_async else self.client
        response = client.chat.completions.create(
            model=self.model_name,
            messages=messages_api_format,
            temperature=inf_gen_config.temperature,
            top_p=inf_gen_config.top_p,
            max_completion_tokens=inf_gen_config.max_tokens,
            seed=inf_gen_config.seed,
            stop=inf_gen_config.stop_sequences,
            # NOTE: top_k is not supported by OpenAI's API
            # NOTE: repetition_penalty is not supported by OpenAI's API
        )
        return response

    async def generate_response(
        self, conv: Conversation, inf_gen_config: InferenceGenerationConfig
    ) -> LLMChatResponse:
        assert self.client is not None, "Client is not initialized."
        messages_api_format: list[dict] = self._convert_conv_to_api_format(conv)
        response = await self._call_api(messages_api_format, inf_gen_config, use_async=True)
        parsed_response = self._parse_api_output(response)
        return parsed_response

    async def batch_generate_response(
        self, convs: list[Conversation], inf_gen_config: InferenceGenerationConfig
    ) -> list[LLMChatResponse]:
        if self.use_api:
            # When using api, we can use the parent class implementation
            # return await super().batch_generate_response(convs, inf_gen_config)
            parsed_responses = await asyncio.gather(
                *[self.generate_response(conv, inf_gen_config) for conv in convs]
            )
            return parsed_responses
        else:
            sampling_params = SamplingParams(
                temperature=inf_gen_config.temperature,
                top_p=inf_gen_config.top_p,
                top_k=inf_gen_config.top_k,
                repetition_penalty=inf_gen_config.repetition_penalty,
                stop=inf_gen_config.stop_sequences + self.ADDITIONAL_STOP,
                max_tokens=inf_gen_config.max_tokens,
                seed=inf_gen_config.seed,
            )
            prompts = [
                self.tokenizer.apply_chat_template(
                    self._convert_conv_to_api_format(conv), tokenize=False, add_generation_prompt=True
                )
                for conv in convs
            ]

            if self.lora_path is None:
                lora_request = None
            else:
                # https://docs.vllm.ai/en/latest/features/lora.html
                # Arguments to LoRARequest are: (a human-identifiable name, a unique id for LoRA module,
                # and the path to the LoRA weights)
                unique_id = uuid.uuid4().int % (2**32)  # Unique 32-bit integer
                lora_request = LoRARequest("lora", unique_id, self.lora_path)

            responses = self.llm.generate(prompts, sampling_params, lora_request=lora_request)
            parsed_responses = [self._parse_batch_vllm_output(response) for response in responses]
            return parsed_responses

    def _count_tokens(self, messages_api_format: list[dict]) -> int:
        """No need to count tokens for vLLM models"""
        return 0
