import asyncio
import json
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple

from deputydev_core.utils.app_logger import AppLogger
from deputydev_core.utils.config_manager import ConfigManager
from types_aiobotocore_bedrock_runtime.type_defs import (
    InvokeModelResponseTypeDef,
    InvokeModelWithResponseStreamResponseTypeDef,
)

from app.backend_common.models.dto.message_thread_dto import (
    ContentBlockCategory,
    LLModels,
    LLMUsage,
    MessageThreadActor,
    MessageThreadDTO,
    ResponseData,
    TextBlockContent,
    TextBlockData,
    ToolUseRequestContent,
    ToolUseRequestData,
    ToolUseResponseContent,
    ToolUseResponseData,
)
from app.backend_common.service_clients.bedrock.bedrock import BedrockServiceClient
from app.backend_common.services.llm.base_llm_provider import BaseLLMProvider
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
from app.backend_common.services.llm.providers.anthropic.dataclasses.main import (
    AnthropicNonStreamingContentResponse,
    AnthropicResponseTypes,
)
from app.common.constants.constants import LLMProviders


class Anthropic(BaseLLMProvider):
    def __init__(self):
        super().__init__(LLMProviders.ANTHROPIC.value)
        self.anthropic_client = None
        self.model_settings: Dict[str, Any] = ConfigManager.configs["LLM_MODELS"]["CLAUDE_3_POINT_5_SONNET"]

    def get_conversation_turns(self, previous_responses: List[MessageThreadDTO]) -> List[ConversationTurn]:
        """
        Formats the conversation as required by the specific LLM.
        Args:
            previous_responses (List[MessageThreadDTO]): The previous conversation turns.
        Returns:
            List[ConversationTurn]: The formatted conversation turns.
        """
        conversation_turns: List[ConversationTurn] = []
        for message in previous_responses:
            role = ConversationRole.USER if message.actor == MessageThreadActor.USER else ConversationRole.ASSISTANT
            content: List[Dict[str, Any]] = []
            for message_data in message.message_data:
                content_data = message_data.content
                if isinstance(content_data, TextBlockContent):
                    content.append(
                        {
                            "type": "text",
                            "text": content_data.text,
                        }
                    )
                elif isinstance(content_data, ToolUseResponseContent):
                    content.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": content_data.tool_use_id,
                            "content": content_data.response,
                        }
                    )
                else:
                    content.append(
                        {
                            "type": "tool_use",
                            "name": content_data.tool_name,
                            "id": content_data.tool_use_id,
                            "input": content_data.tool_input,
                        }
                    )
            conversation_turns.append(ConversationTurn(role=role, content=content))

        return conversation_turns

    def build_llm_payload(
        self,
        prompt: Optional[UserAndSystemMessages] = None,
        tool_use_response: Optional[ToolUseResponseData] = None,
        previous_responses: List[MessageThreadDTO] = [],
        tools: Optional[List[ConversationTool]] = None,
        cache_config: PromptCacheConfig = PromptCacheConfig(tools=False, system_message=False, conversation=False),
    ) -> Dict[str, Any]:

        # create conversation array
        messages: List[ConversationTurn] = self.get_conversation_turns(previous_responses)

        # add system and user messages to conversation
        if prompt:
            user_message = ConversationTurn(role=ConversationRole.USER, content=prompt.user_message)
            messages.append(user_message)

        # add tool result to conversation
        if tool_use_response:
            tool_message = ConversationTurn(
                role=ConversationRole.USER,
                content=[
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use_response.content.tool_use_id,
                        "content": tool_use_response.content.response,
                    }
                ],
            )
            messages.append(tool_message)

        # create tools sorted by name
        tools = sorted(tools, key=lambda x: x.name) if tools else []

        # create body
        llm_payload = {
            "anthropic_version": self.model_settings["VERSION"],
            "max_tokens": self.model_settings["MAX_TOKENS"],
            "system": prompt.system_message if prompt else None,
            "messages": [message.model_dump(mode="json") for message in messages],
            "tools": [tool.model_dump(mode="json") for tool in tools],
        }
        print(llm_payload)
        return llm_payload

    async def _get_service_client(self):
        if not self.anthropic_client:
            self.anthropic_client = BedrockServiceClient()
        return self.anthropic_client

    async def _parse_non_streaming_response(self, response: InvokeModelResponseTypeDef) -> NonStreamingResponse:
        body: bytes = await response["body"].read()  # type: ignore
        llm_response = json.loads(body.decode("utf-8"))  # type: ignore

        # validate content array once we have the response

        content_array: List[AnthropicNonStreamingContentResponse] = llm_response["content"]

        non_streaming_content_blocks: List[ResponseData] = []
        for content_block in content_array:
            if content_block["type"] == AnthropicResponseTypes.TEXT:
                non_streaming_content_blocks.append(
                    TextBlockData(
                        type=ContentBlockCategory.TEXT_BLOCK,
                        content=TextBlockContent(text=content_block["text"]),
                    )
                )
            elif content_block["type"] == AnthropicResponseTypes.TOOL_USE:
                non_streaming_content_blocks.append(
                    ToolUseRequestData(
                        type=ContentBlockCategory.TOOL_USE_REQUEST,
                        content=ToolUseRequestContent(
                            tool_input=content_block["input"],
                            tool_name=content_block["name"],
                            tool_use_id=content_block["id"],
                        ),
                    )
                )

        return NonStreamingResponse(
            content=non_streaming_content_blocks,
            usage=LLMUsage(input=llm_response["usage"]["input_tokens"], output=llm_response["usage"]["output_tokens"]),
            type=LLMCallResponseTypes.NON_STREAMING,
        )

    def _get_parsed_stream_event(
        self, event: Dict[str, Any], current_running_block_type: Optional[ContentBlockCategory] = None
    ) -> Tuple[Optional[StreamingEvent], Optional[ContentBlockCategory], Optional[LLMUsage]]:
        """
        Parses the streaming event and returns the corresponding content block and usage.

        Args:
            event (Dict[str, Any]): The event to parse.
            current_running_block_type (ContentBlockCategory): The current running block type.

        Returns:
            Tuple[Optional[StreamingContentBlock], Optional[LLMUsage]]: The content block and usage.
        """
        usage = LLMUsage(input=0, output=0, cache_read=0, cache_write=0)

        # message start blocks and delta blocks for usage tracking
        if event["type"] == "message_start":
            usage.input += event["message"]["usage"].get("input_tokens", 0)
            usage.output += event["message"]["usage"].get("output_tokens", 0)
            return None, None, usage

        if event["type"] == "message_delta":
            usage.input += event["usage"].get("input_tokens", 0)
            usage.output += event["usage"].get("output_tokens", 0)
            return None, None, usage

        # parsers for tool use request blocks
        if event["type"] == "content_block_start" and event["content_block"]["type"] == "tool_use":
            return (
                ToolUseRequestStart(
                    type=StreamingEventType.TOOL_USE_REQUEST_START,
                    content=ToolUseRequestStartContent(
                        tool_name=event["content_block"]["name"],
                        tool_use_id=event["content_block"]["id"],
                    ),
                ),
                ContentBlockCategory.TOOL_USE_REQUEST,
                None,
            )

        if event["type"] == "content_block_delta" and event["delta"]["type"] == "input_json_delta":
            return (
                ToolUseRequestDelta(
                    type=StreamingEventType.TOOL_USE_REQUEST_DELTA,
                    content=ToolUseRequestDeltaContent(
                        input_params_json_delta=event["delta"]["partial_json"],
                    ),
                ),
                ContentBlockCategory.TOOL_USE_REQUEST,
                None,
            )

        if (
            event["type"] == "content_block_stop"
            and current_running_block_type == ContentBlockCategory.TOOL_USE_REQUEST
        ):
            return (
                ToolUseRequestEnd(
                    type=StreamingEventType.TOOL_USE_REQUEST_END,
                ),
                ContentBlockCategory.TOOL_USE_REQUEST,
                None,
            )

        # parsers for text blocks
        if event["type"] == "content_block_start" and event["content_block"]["type"] == "text":
            return (
                TextBlockStart(
                    type=StreamingEventType.TEXT_BLOCK_START,
                ),
                ContentBlockCategory.TEXT_BLOCK,
                None,
            )

        if event["type"] == "content_block_delta" and event["delta"]["type"] == "text_delta":
            return (
                TextBlockDelta(
                    type=StreamingEventType.TEXT_BLOCK_DELTA,
                    content=TextBlockDeltaContent(
                        text=event["delta"]["text"],
                    ),
                ),
                ContentBlockCategory.TEXT_BLOCK,
                None,
            )

        if event["type"] == "content_block_stop" and current_running_block_type == ContentBlockCategory.TEXT_BLOCK:
            return (
                TextBlockEnd(
                    type=StreamingEventType.TEXT_BLOCK_END,
                ),
                ContentBlockCategory.TEXT_BLOCK,
                None,
            )

        return None, None, None

    async def _parse_streaming_response(
        self, response: InvokeModelWithResponseStreamResponseTypeDef
    ) -> StreamingResponse:
        usage = LLMUsage(input=0, output=0, cache_read=0, cache_write=0)
        streaming_completed: bool = False
        accumulated_events: List[StreamingEvent] = []

        async def stream_content() -> AsyncIterator[StreamingEvent]:
            nonlocal usage
            nonlocal streaming_completed
            nonlocal accumulated_events
            current_running_block_type: Optional[ContentBlockCategory] = None
            async for event in response["body"]:
                chunk = json.loads(event["chunk"]["bytes"])

                print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
                print(chunk)
                print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")

                # yield content block delta

                try:
                    event_block, event_block_category, event_usage = self._get_parsed_stream_event(
                        chunk, current_running_block_type
                    )
                    if event_usage:
                        usage += event_usage
                    if event_block:
                        current_running_block_type = event_block_category
                        accumulated_events.append(event_block)
                        yield event_block
                except Exception:
                    # gracefully handle new events. See Anthropic docs here - https://docs.anthropic.com/en/api/messages-streaming#other-events
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

        return StreamingResponse(
            content=stream_content(), usage=asyncio.create_task(get_usage()), type=LLMCallResponseTypes.STREAMING, accumulated_events=asyncio.create_task(get_accumulated_events())
        )

    async def call_service_client(
        self, llm_payload: Dict[str, Any], model: LLModels, stream: bool = False, response_type: Optional[str] = None
    ) -> UnparsedLLMCallResponse:
        anthropic_client = await self._get_service_client()
        AppLogger.log_debug(json.dumps(llm_payload))
        model_config = self._get_model_config(model)
        if stream is False:
            response = await anthropic_client.get_llm_response(llm_payload=llm_payload, model=model_config["NAME"])
            return await self._parse_non_streaming_response(response)
        else:
            response = await anthropic_client.get_llm_stream_response(
                llm_payload=llm_payload, model=model_config["NAME"]
            )
            return await self._parse_streaming_response(response)
