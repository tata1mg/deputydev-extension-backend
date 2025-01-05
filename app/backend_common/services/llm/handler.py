import asyncio
from typing import Dict, List, Tuple

from app.backend_common.services.llm.base_llm_provider import BaseLLMProvider
from app.backend_common.services.llm.providers.anthropic_llm import Anthropic
from app.backend_common.services.llm.providers.dataclass.main import (
    LLMCallResponse,
    LLMMeta,
    LLMUsage,
)
from app.backend_common.services.llm.providers.openai_llm import OpenaiLLM
from app.common.constants.constants import LLModels
from app.common.exception import RetryException
from app.common.services.prompt.base_prompt import BasePrompt
from app.common.utils.app_logger import AppLogger
from app.common.utils.config_manager import ConfigManager


class LLMHandler:
    model_to_provider_class_map = {
        LLModels.CLAUDE_3_POINT_5_SONNET: Anthropic,
        LLModels.GPT_4O: OpenaiLLM,
    }

    def __init__(self, prompt: BasePrompt):
        self.prompt = prompt

    async def get_llm_response_data(self, previous_responses: List[Dict[str, str]]) -> LLMCallResponse:
        detected_llm = self.prompt.model_name

        if detected_llm not in self.model_to_provider_class_map:
            raise ValueError(f"LLM model {detected_llm} not supported")

        client = self.model_to_provider_class_map[detected_llm]()
        model_config = ConfigManager.configs["LLM_MODELS"].get(detected_llm.value)
        prompt = self.prompt.get_prompt()
        llm_message = client.build_llm_message(prompt, previous_responses)

        parsed_response, input_tokens, output_tokens = await self.get_llm_response(
            client=client, messages=llm_message, model=model_config.get("NAME"), structure_type="text"
        )

        return LLMCallResponse(
            raw_prompt=prompt["user_message"],
            raw_llm_response=parsed_response,
            parsed_llm_data=self.prompt.get_parsed_result(parsed_response),
            llm_meta=LLMMeta(
                llm_model=detected_llm,
                prompt_type=self.prompt.prompt_type,
                token_usage=LLMUsage(input=input_tokens, output=output_tokens),
            ),
        )

    async def get_llm_response(
        self,
        client: BaseLLMProvider,
        messages: str,
        model: str,
        structure_type: str,
        max_retry: int = 2,
    ) -> Tuple[str, int, int]:
        for i in range(0, max_retry):
            try:
                print(f"Calling service client {i}")
                llm_response = await client.call_service_client(messages, model, structure_type)
                print("LLM response", llm_response)
                return await client.parse_response(llm_response)
            except Exception as e:
                AppLogger.log_warn(f"Retry {i + 1}/{max_retry}  Error while fetching data from LLM: {e}")
                last_exception = e
                await asyncio.sleep(2)
            if i + 1 == max_retry:
                raise RetryException(f"Retried due to llm client call failed {last_exception}")

        return "", 0, 0
