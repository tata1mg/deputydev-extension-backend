import asyncio
import traceback
from typing import List, Optional

from deputydev_core.utils.app_logger import AppLogger

from app.backend_common.models.dto.message_thread_dto import (
    LLModels,
    MessageDataTypes,
    MessageThreadActor,
    MessageType,
    ToolUseResponseMessageData,
)
from app.backend_common.repository.message_threads.repository import (
    MessageThreadsRepository,
)
from app.backend_common.services.llm.base_llm_provider import BaseLLMProvider
from app.backend_common.services.llm.dataclasses.main import (
    ConversationRole,
    ConversationTool,
    ConversationTurn,
    LLMCallResponseTypes,
    NonStreamingParsedLLMCallResponse,
    ParsedLLMCallResponse,
    PromptCacheConfig,
    StreamingParsedLLMCallResponse,
    UnparsedLLMCallResponse,
    UserAndSystemMessages,
)
from app.backend_common.services.llm.prompts.base_prompt import BasePrompt
from app.backend_common.services.llm.providers.anthropic.llm_provider import Anthropic
from app.backend_common.services.llm.providers.open_ai_reasioning_llm import (
    OpenAIReasoningLLM,
)
from app.backend_common.services.llm.providers.openai_llm import OpenaiLLM
from app.common.exception import RetryException


class LLMHandler:
    model_to_provider_class_map = {
        LLModels.CLAUDE_3_POINT_5_SONNET: Anthropic,
        LLModels.GPT_4O: OpenaiLLM,
        LLModels.GPT_40_MINI: OpenaiLLM,
        LLModels.GPT_O1_MINI: OpenAIReasoningLLM,
    }

    def __init__(
        self,
        prompt_handler: Optional[BasePrompt] = None,
        tools: Optional[List[ConversationTool]] = None,
        cache_config: PromptCacheConfig = PromptCacheConfig(tools=False, system_message=False, conversation=False),
        stream: bool = False,
    ):
        self.prompt_handler = prompt_handler
        self.tools = tools
        self.cache_config = cache_config
        self.stream = stream

    async def get_llm_response(
        self,
        client: BaseLLMProvider,
        model: LLModels,
        prompt: Optional[UserAndSystemMessages] = None,
        tool_use_response: Optional[ToolUseResponseMessageData] = None,
        previous_responses: List[ConversationTurn] = [],
        max_retry: int = 2,
    ) -> UnparsedLLMCallResponse:
        for i in range(0, max_retry):
            try:
                llm_payload = client.build_llm_payload(
                    prompt=prompt,
                    tool_use_response=tool_use_response,
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

    async def parse_llm_response_data(self, llm_response: UnparsedLLMCallResponse) -> ParsedLLMCallResponse:
        if llm_response.type == LLMCallResponseTypes.STREAMING:
            parsed_stream = await self.prompt_handler.get_parsed_streaming_events(llm_response)
            return StreamingParsedLLMCallResponse(
                type=llm_response.type,
                content=llm_response.content,
                parsed_content=parsed_stream,
                usage=llm_response.usage,
                model_used=detected_llm,
                prompt_vars={},
                prompt_id=self.prompt_handler.prompt_type,
            )
        else:
            parsed_content = self.prompt_handler.get_parsed_result(llm_response)
            return NonStreamingParsedLLMCallResponse(
                type=llm_response.type,
                content=llm_response.content,
                parsed_content=parsed_content,
                usage=llm_response.usage,
                model_used=detected_llm,
                prompt_vars={},
                prompt_id=self.prompt_handler.prompt_type,
            )

    async def get_parsed_llm_response_data(
        self, previous_responses: List[ConversationTurn] = []
    ) -> ParsedLLMCallResponse:
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

        if llm_response.type == LLMCallResponseTypes.STREAMING:
            parsed_stream = await self.prompt_handler.get_parsed_streaming_events(llm_response)
            return StreamingParsedLLMCallResponse(
                type=llm_response.type,
                content=llm_response.content,
                parsed_content=parsed_stream,
                usage=llm_response.usage,
                model_used=detected_llm,
                prompt_vars={},
                prompt_id=self.prompt_handler.prompt_type,
            )
        else:
            parsed_content = self.prompt_handler.get_parsed_result(llm_response)
            return NonStreamingParsedLLMCallResponse(
                type=llm_response.type,
                content=llm_response.content,
                parsed_content=parsed_content,
                usage=llm_response.usage,
                model_used=detected_llm,
                prompt_vars={},
                prompt_id=self.prompt_handler.prompt_type,
            )

    async def continue_response_with_tool_use(
        self,
        tool_use_response: ToolUseResponseMessageData,
        session_id: str,
    ) -> ParsedLLMCallResponse:

        session_messages = await MessageThreadsRepository.get_message_threads_for_session(session_id=session_id)
        filtered_messages = [message for message in session_messages if message.message_type == MessageType.RESPONSE]

        detected_llm: Optional[LLModels] = None
        tool_use_request_message_id = None
        for message in filtered_messages:
            for data in message.message_data:
                if data.type == MessageDataTypes.TOOL_USE_REQUEST and data.tool_use_id == tool_use_response.tool_use_id:
                    tool_use_request_message_id = message.id
                    detected_llm = message.llm_model
                    break

        if not tool_use_request_message_id or not detected_llm:
            raise ValueError(
                f"Tool use request message not found for tool use response id {tool_use_response.tool_use_id}"
            )

        previous_messages: List[ConversationTurn] = []
        for message in session_messages:
            if message.id <= tool_use_request_message_id:
                for data in message.message_data:
                    if data.type == MessageDataTypes.TEXT:
                        previous_messages.append(
                            ConversationTurn(
                                role=ConversationRole.USER
                                if message.actor == MessageThreadActor.USER
                                else ConversationRole.ASSISTANT,
                                content=data.text,
                            )
                        )
                    elif data.type == MessageDataTypes.TOOL_USE_REQUEST:
                        previous_messages.append(
                            ConversationTurn(
                                role=ConversationRole.USER
                                if message.actor == MessageThreadActor.USER
                                else ConversationRole.ASSISTANT,
                                content=data.tool_name,
                            )
                        )
                    elif data.type == MessageDataTypes.TOOL_USE_RESPONSE:
                        previous_messages.append(
                            ConversationTurn(
                                role=ConversationRole.USER
                                if message.actor == MessageThreadActor.USER
                                else ConversationRole.ASSISTANT,
                                content=str(data.response),
                            )
                        )

        client = self.model_to_provider_class_map[detected_llm]()
        llm_response = await self.get_llm_response(
            client=client,
            tool_use_response=tool_use_response,
            model=detected_llm,
            previous_responses=previous_messages,
        )

        if llm_response.type == LLMCallResponseTypes.STREAMING:
            parsed_stream = await self.prompt_handler.get_parsed_streaming_events(llm_response)
            return StreamingParsedLLMCallResponse(
                type=llm_response.type,
                content=llm_response.content,
                parsed_content=parsed_stream,
                usage=llm_response.usage,
                model_used=detected_llm,
                prompt_vars={},
                prompt_id=self.prompt_handler.prompt_type,
            )
        else:
            parsed_content = self.prompt_handler.get_parsed_result(llm_response)
            return NonStreamingParsedLLMCallResponse(
                type=llm_response.type,
                content=llm_response.content,
                parsed_content=parsed_content,
                usage=llm_response.usage,
                model_used=detected_llm,
                prompt_vars={},
                prompt_id=self.prompt_handler.prompt_type,
            )
