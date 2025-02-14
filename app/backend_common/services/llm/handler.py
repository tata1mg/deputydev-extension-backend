import asyncio
import traceback
from typing import List, Optional, Union

from app.backend_common.services.llm.base_llm_provider import BaseLLMProvider
from app.backend_common.services.llm.dataclasses.main import (
    ConversationTool,
    ConversationTurn,
    LLMCallResponse,
    LLMMeta,
    LLModels,
    NonStreamingResponse,
    PromptCacheConfig,
    StreamingResponse,
    UserAndSystemMessages,
)
from app.backend_common.services.llm.prompts.base_prompt import BasePrompt
from app.backend_common.services.llm.providers.anthropic_llm import Anthropic
from app.backend_common.services.llm.providers.open_ai_reasioning_llm import (
    OpenAIReasoningLLM,
)
from app.backend_common.services.llm.providers.openai_llm import OpenaiLLM
from app.common.exception import RetryException
from app.common.utils.app_logger import AppLogger


class LLMHandler:
    model_to_provider_class_map = {
        LLModels.CLAUDE_3_POINT_5_SONNET: Anthropic,
        LLModels.GPT_4O: OpenaiLLM,
        LLModels.GPT_40_MINI: OpenaiLLM,
        LLModels.GPT_O1_MINI: OpenAIReasoningLLM,
    }

    def __init__(
        self,
        prompt_handler: BasePrompt,
        tools: Optional[List[ConversationTool]] = None,
        cache_config: PromptCacheConfig = PromptCacheConfig(tools=False, system_message=False, conversation=False),
        stream: bool = False,
    ):
        self.prompt_handler = prompt_handler
        self.tools = tools
        self.cache_config = cache_config
        self.stream = stream

    async def get_llm_response_data(self, previous_responses: List[ConversationTurn] = []) -> LLMCallResponse:
        detected_llm = self.prompt_handler.model_name

        if detected_llm not in self.model_to_provider_class_map:
            raise ValueError(f"LLM model {detected_llm} not supported")

        client = self.model_to_provider_class_map[detected_llm]()
        prompt = self.prompt_handler.get_prompt()

        llm_response = await self.get_llm_response(
            client=client,
            prompt=prompt,
            model=detected_llm,
            previous_responses=previous_responses,
        )

        return LLMCallResponse(
            raw_prompt=prompt.user_message,
            raw_llm_response=llm_response.content,
            parsed_llm_data=self.prompt_handler.get_parsed_result(llm_response.content)
            if isinstance(llm_response, NonStreamingResponse)
            else None,
            llm_meta=LLMMeta(
                llm_model=detected_llm,
                prompt_type=self.prompt_handler.prompt_type,
                token_usage=llm_response.usage,
            ),
        )

    async def get_llm_response(
        self,
        client: BaseLLMProvider,
        prompt: UserAndSystemMessages,
        model: LLModels,
        previous_responses: List[ConversationTurn] = [],
        max_retry: int = 2,
    ) -> Union[StreamingResponse, NonStreamingResponse]:
        for i in range(0, max_retry):
            try:
                llm_payload = client.build_llm_payload(
                    prompt=prompt,
                    previous_responses=previous_responses,
                    tools=self.tools,
                    cache_config=self.cache_config,
                )
                llm_response = await client.call_service_client(llm_payload, model, self.stream)
                return llm_response
            except Exception as e:
                AppLogger.log_debug(traceback.format_exc())
                print(traceback.format_exc())
                AppLogger.log_warn(f"Retry {i + 1}/{max_retry}  Error while fetching data from LLM: {e}")
                await asyncio.sleep(2)
        raise RetryException(f"Failed to get response from LLM after {max_retry} retries")
