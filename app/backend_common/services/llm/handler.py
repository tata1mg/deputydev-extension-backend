import asyncio
import traceback
from typing import Dict, List, Optional

from deputydev_core.utils.app_logger import AppLogger

from app.backend_common.models.dto.message_thread_dto import (
    LLModels,
    MessageDataTypes,
    MessageThreadActor,
    MessageThreadDTO,
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
        prompt_handler_map: Dict[str, BasePrompt],
        cache_config: PromptCacheConfig = PromptCacheConfig(tools=False, system_message=False, conversation=False),
    ):
        self.prompt_handler_map = prompt_handler_map
        self.cache_config = cache_config

    async def get_llm_response(
        self,
        client: BaseLLMProvider,
        model: LLModels,
        prompt: Optional[UserAndSystemMessages] = None,
        tools: Optional[List[ConversationTool]] = None,
        tool_use_response: Optional[ToolUseResponseMessageData] = None,
        previous_responses: List[ConversationTurn] = [],
        max_retry: int = 2,
        stream: bool = False,
    ) -> UnparsedLLMCallResponse:
        for i in range(0, max_retry):
            try:
                llm_payload = client.build_llm_payload(
                    prompt=prompt,
                    tool_use_response=tool_use_response,
                    previous_responses=previous_responses,
                    tools=tools,
                    cache_config=self.cache_config,
                )
                llm_response = await client.call_service_client(llm_payload, model, stream=stream)
                return llm_response
            except Exception as e:
                AppLogger.log_debug(traceback.format_exc())
                print(traceback.format_exc())
                AppLogger.log_warn(f"Retry {i + 1}/{max_retry}  Error while fetching data from LLM: {e}")
                await asyncio.sleep(2)
        raise RetryException(f"Failed to get response from LLM after {max_retry} retries")

    async def parse_llm_response_data(
        self, llm_response: UnparsedLLMCallResponse, prompt_handler: BasePrompt
    ) -> ParsedLLMCallResponse:
        if llm_response.type == LLMCallResponseTypes.STREAMING:
            parsed_stream = await prompt_handler.get_parsed_streaming_events(llm_response)
            return StreamingParsedLLMCallResponse(
                type=llm_response.type,
                content=llm_response.content,
                parsed_content=parsed_stream,
                usage=llm_response.usage,
                model_used=prompt_handler.model_name,
                prompt_vars={},
                prompt_id=prompt_handler.prompt_type,
            )
        else:
            parsed_content = prompt_handler.get_parsed_result(llm_response)
            return NonStreamingParsedLLMCallResponse(
                type=llm_response.type,
                content=llm_response.content,
                parsed_content=parsed_content,
                usage=llm_response.usage,
                model_used=prompt_handler.model_name,
                prompt_vars={},
                prompt_id=prompt_handler.prompt_type,
            )

    async def start_llm_query(
        self,
        prompt_handler: BasePrompt,
        tools: Optional[List[ConversationTool]] = None,
        previous_responses: List[ConversationTurn] = [],
        stream: bool = False,
    ) -> ParsedLLMCallResponse:
        detected_llm = prompt_handler.model_name

        if detected_llm not in self.model_to_provider_class_map:
            raise ValueError(f"LLM model {detected_llm} not supported")

        client = self.model_to_provider_class_map[detected_llm]()
        prompt = prompt_handler.get_prompt()

        llm_response = await self.get_llm_response(
            client=client,
            prompt=prompt,
            tools=tools,
            model=detected_llm,
            previous_responses=previous_responses,
            stream=stream,
        )

        return await self.parse_llm_response_data(llm_response=llm_response, prompt_handler=prompt_handler)

    async def generate_previous_messages(self, session_messages: List[MessageThreadDTO]) -> List[ConversationTurn]:
        """
        Generate previous messages from session messages

        Parameters:
            :param session_messages: List of session messages

        Returns:
            :return: List of conversation turns
        """
        previous_messages: List[ConversationTurn] = []
        for message in session_messages:
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
        return previous_messages

    async def submit_tool_use_response(
        self,
        session_id: str,
        tool_use_response: ToolUseResponseMessageData,
        tools: Optional[List[ConversationTool]] = None,
        stream: bool = False,
    ) -> ParsedLLMCallResponse:
        """
        Submit tool use response to LLM

        Parameters:
            :param session_id: Session id
            :param tool_use_response: Tool use response data
            :param tools: List of tools
            :param stream: Stream response
            :return: Parsed LLM response

        Returns:
            ParsedLLMCallResponse: Parsed LLM response
        """

        session_messages = await MessageThreadsRepository.get_message_threads_for_session(session_id=session_id)
        filtered_messages = [message for message in session_messages if message.message_type == MessageType.RESPONSE]

        detected_llm: Optional[LLModels] = None
        tool_use_request_message_id = None
        detected_prompt_handler: Optional[BasePrompt] = None
        for message in filtered_messages:
            for data in message.message_data:
                if data.type == MessageDataTypes.TOOL_USE_REQUEST and data.tool_use_id == tool_use_response.tool_use_id:
                    tool_use_request_message_id = message.id
                    detected_llm = message.llm_model
                    detected_prompt_handler = self.prompt_handler_map.get(message.prompt_type)
                    break

        if not tool_use_request_message_id or not detected_llm:
            raise ValueError(
                f"Tool use request message not found for tool use response id {tool_use_response.tool_use_id}"
            )

        if not detected_prompt_handler:
            raise ValueError("Prompt handler not found for prompt type")

        previous_messages = await self.generate_previous_messages(
            [message for message in session_messages if message.id <= tool_use_request_message_id]
        )

        client = self.model_to_provider_class_map[detected_llm]()
        llm_response = await self.get_llm_response(
            client=client,
            tool_use_response=tool_use_response,
            tools=tools,
            model=detected_llm,
            previous_responses=previous_messages,
            stream=stream,
        )

        return await self.parse_llm_response_data(llm_response=llm_response, prompt_handler=detected_prompt_handler)
