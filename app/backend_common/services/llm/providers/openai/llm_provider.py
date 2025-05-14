import asyncio
from typing import Any, Dict, List, Optional, Literal, AsyncIterator
from openai.types.responses.response_stream_event import ResponseStreamEvent
from deputydev_core.utils.config_manager import ConfigManager
from openai.types.chat import ChatCompletion
from app.backend_common.services.llm.dataclasses.main import (
    ConversationRole,
    ConversationTool,
    ConversationTurn,
    LLMCallResponseTypes,
    NonStreamingResponse,
    PromptCacheConfig,
    StreamingEvent,
    StreamingEventType,
    StreamingResponse,
    TextBlockDelta,
    TextBlockDeltaContent,
    TextBlockEnd,
    TextBlockStart,
    ToolUseRequestDelta,
    ToolUseRequestDeltaContent,
    ToolUseRequestEnd,
    ToolUseRequestStart,
    ToolUseRequestStartContent,
    UnparsedLLMCallResponse,
    UserAndSystemMessages,
)
from app.backend_common.constants.constants import LLMProviders
from app.backend_common.models.dto.message_thread_dto import (
    LLModels,
    LLMUsage,
    MessageThreadDTO,
    ResponseData,
    TextBlockContent,
    TextBlockData,
    ToolUseRequestContent,
    ToolUseRequestData,
    ToolUseResponseData,
    ContentBlockCategory,
)
from app.backend_common.service_clients.openai.openai import OpenAIServiceClient
from app.backend_common.services.llm.base_llm_provider import BaseLLMProvider
from app.backend_common.services.llm.dataclasses.main import (
    ConversationTool,
    NonStreamingResponse,
    PromptCacheConfig,
    UnparsedLLMCallResponse,
    UserAndSystemMessages,
)


class OpenAI(BaseLLMProvider):
    def __init__(self):
        super().__init__(LLMProviders.OPENAI.value)
        self.anthropic_client = None

    def build_llm_payload(
        self,
        llm_model,
        prompt: Optional[UserAndSystemMessages] = None,
        tool_use_response: Optional[ToolUseResponseData] = None,
        previous_responses: List[MessageThreadDTO] = [],
        tools: Optional[List[ConversationTool]] = None,
        cache_config: PromptCacheConfig = PromptCacheConfig(
            tools=True, system_message=True, conversation=True
        ),  # by default, OpenAI uses caching, we cannot configure it
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Formats the conversation for OpenAI's GPT model.

        Args:
            prompt (Dict[str, str]): A prompt object.
            previous_responses (List[Dict[str, str]] ): previous messages to pass to LLM

        Returns:
            List[Dict[str, str]]: A formatted list of message dictionaries.
        """
        if tools or tool_use_response:
            pass

        if previous_responses:
            pass

        if prompt is None:
            raise ValueError("Prompt is required for OpenAI")

        conversation_messages = [
            {"role": "system", "content": prompt.system_message},
            {"role": "user", "content": prompt.user_message},
        ]
        return {
            "conversation_messages": conversation_messages,
        }

    def _parse_non_streaming_response(self, response: ChatCompletion) -> NonStreamingResponse:
        """
        Parses the response from OpenAI's GPT model.

        Args:
            response : The raw response from the GPT model.

        Returns:
            NonStreamingResponse: Parsed response
        """
        non_streaming_content_blocks: List[ResponseData] = []

        if response.choices[0].message.content:
            non_streaming_content_blocks.append(
                TextBlockData(content=TextBlockContent(text=response.choices[0].message.content))
            )

        # though tool use is not supported for now, parser is implemented for tool response
        # TODO: Test this
        if response.choices[0].message.tool_calls:
            for tool_call in response.choices[0].message.tool_calls:
                if tool_call.type != "function":
                    continue

                non_streaming_content_blocks.append(
                    ToolUseRequestData(
                        content=ToolUseRequestContent(
                            tool_input=tool_call.function.arguments,
                            tool_name=tool_call.function.name,
                            tool_use_id=tool_call.id,
                        )
                    )
                )

        return NonStreamingResponse(
            content=non_streaming_content_blocks,
            usage=(
                LLMUsage(
                    input=response.usage.prompt_tokens,
                    output=response.usage.completion_tokens,
                )
                if response.usage
                else LLMUsage(input=0, output=0)
            ),
        )

    async def call_service_client(
        self,
        llm_payload: Dict[str, Any],
        model: LLModels,
        stream: bool = False,
        response_type: Literal["text", "json_object", "json_schema"] = None,
    ) -> UnparsedLLMCallResponse:
        """
        Calls the OpenAI service client.

        Args:
            messages (List[Dict[str, str]]): Formatted conversation messages.

        Returns:
            str: The response from the GPT model.
        """
        if not response_type:
            response_type = "text"
        model_config = self._get_model_config(model)
        if stream:
            response = await OpenAIServiceClient().get_llm_stream_response(
                conversation_messages=llm_payload["conversation_messages"],
                model=model_config["NAME"],
                response_type=response_type,
            )
            return self._parse_streaming_response(response)
        else:
            response = await OpenAIServiceClient().get_llm_non_stream_response(
                conversation_messages=llm_payload["conversation_messages"],
                model=model_config["NAME"],
                response_type=response_type,
            )
            return self._parse_non_streaming_response(response)

    async def _parse_streaming_response(self, response: AsyncIterator[ResponseStreamEvent]) -> StreamingResponse:
        usage = LLMUsage(input=0, output=0, cache_read=0, cache_write=0)
        streaming_completed = False
        accumulated_events = []

        async def stream_content() -> AsyncIterator[StreamingEvent]:
            nonlocal usage
            nonlocal streaming_completed
            nonlocal accumulated_events
            async for event in response:
                try:
                    event_block, event_block_category, event_usage = await self._get_parsed_stream_event(event)
                    if event_usage:
                        usage += event_usage
                    if event_block:
                        accumulated_events.append(event_block)
                        yield event_block
                except Exception:
                    pass

            streaming_completed = True

        async def get_usage() -> LLMUsage:
            nonlocal usage
            nonlocal streaming_completed
            while not streaming_completed:
                await asyncio.sleep(0.1)

            return usage

        async def get_accumulated_events() -> List[StreamingEvent]:
            nonlocal accumulated_events
            nonlocal streaming_completed
            while not streaming_completed:
                await asyncio.sleep(0.1)
            return accumulated_events

        async def close_client():
            nonlocal streaming_completed
            while not streaming_completed:
                await asyncio.sleep(0.1)
            # TODO: close client

        asyncio.create_task(close_client())

        return StreamingResponse(
            content=stream_content(),
            usage=asyncio.create_task(get_usage()),
            type=LLMCallResponseTypes.STREAMING,
            accumulated_events=asyncio.create_task(get_accumulated_events()),
        )

    async def _get_parsed_stream_event(self, event: ResponseStreamEvent):
        usage = LLMUsage(input=0, output=0, cache_read=0, cache_write=0)
        if event.type == "response.done":
            usage.input = event.response.usage.input_token_details.text_tokens
            usage.output = event.response.usage.output_tokens
            usage.cache_read = event.response.usage.input_tokens_details.cached_tokens
            return None, None, usage
        if event.type == "response.output_item.added" and event.item.type == "function_call":
            return (
                ToolUseRequestStart(
                    type=StreamingEventType.TOOL_USE_REQUEST_START,
                    content=ToolUseRequestStartContent(
                        tool_name=event.item.name,
                        tool_use_id=event.item.call_id,
                    ),
                ),
                ContentBlockCategory.TOOL_USE_REQUEST,
                None,
            )
        if event.type == "response.function_call_arguments.delta":
            return (
                ToolUseRequestDelta(
                    type=StreamingEventType.TOOL_USE_REQUEST_DELTA,
                    content=ToolUseRequestDeltaContent(
                        input_params_json_delta=event.delta,
                    ),
                ),
                ContentBlockCategory.TOOL_USE_REQUEST,
                None,
            )
        if event.type == "response.function_call_arguments.done":
            return (
                ToolUseRequestEnd(
                    type=StreamingEventType.TOOL_USE_REQUEST_END,
                ),
                ContentBlockCategory.TOOL_USE_REQUEST,
                None,
            )
        if event.type == "response.output_item.added" and event.item.type == "message":
            return (
                TextBlockStart(
                    type=StreamingEventType.TEXT_BLOCK_START,
                ),
                ContentBlockCategory.TEXT_BLOCK,
                None,
            )
        if event.type == "response.text.delta":
            return (
                TextBlockDelta(
                    type=StreamingEventType.TEXT_BLOCK_DELTA,
                    content=TextBlockDeltaContent(
                        text=event.delta,
                    ),
                ),
                ContentBlockCategory.TEXT_BLOCK,
                None,
            )
        if event.type == "response.text.done":
            return (
                TextBlockEnd(
                    type=StreamingEventType.TEXT_BLOCK_END,
                ),
                ContentBlockCategory.TEXT_BLOCK,
                None,
            )

        return None, None, None
