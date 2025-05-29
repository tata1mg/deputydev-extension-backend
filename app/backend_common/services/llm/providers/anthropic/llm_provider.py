import asyncio
import json
from typing import Any, AsyncIterable, AsyncIterator, Dict, List, Literal, Optional, Tuple, cast

from deputydev_core.utils.app_logger import AppLogger
from types_aiobotocore_bedrock_runtime import BedrockRuntimeClient
from types_aiobotocore_bedrock_runtime.type_defs import (
    InvokeModelResponseTypeDef,
    InvokeModelWithResponseStreamResponseTypeDef,
)

from app.backend_common.constants.constants import LLMProviders
from app.backend_common.models.dto.message_thread_dto import (
    ContentBlockCategory,
    LLModels,
    LLMUsage,
    MessageThreadActor,
    MessageThreadDTO,
    MessageType,
    ResponseData,
    TextBlockContent,
    TextBlockData,
    ToolUseRequestContent,
    ToolUseRequestData,
    ToolUseResponseContent,
    ToolUseResponseData,
    ExtendedThinkingContent,
)
from app.backend_common.service_clients.bedrock.bedrock import BedrockServiceClient
from app.backend_common.services.llm.base_llm_provider import BaseLLMProvider
from app.backend_common.services.llm.dataclasses.main import (
    ChatAttachmentDataWithObjectBytes,
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
    ExtendedThinkingBlockStart,
    ExtendedThinkingBlockDelta,
    ExtendedThinkingBlockDeltaContent,
    ExtendedThinkingBlockEnd,
    ExtendedThinkingBlockEndContent,
    RedactedThinking,
)
from app.backend_common.services.llm.providers.anthropic.dataclasses.main import (
    AnthropicResponseTypes,
)
from app.backend_common.services.chat_file_upload.file_processor import FileProcessor
from app.main.blueprints.one_dev.services.query_solver.dataclasses.main import Attachment


class Anthropic(BaseLLMProvider):
    def __init__(self):
        super().__init__(LLMProviders.ANTHROPIC.value)
        self.anthropic_client = None

    async def get_conversation_turns(
        self,
        previous_responses: List[MessageThreadDTO],
        attachment_data_task_map: Dict[int, asyncio.Task[ChatAttachmentDataWithObjectBytes]],
    ) -> List[ConversationTurn]:
        """
        Formats the conversation as required by the specific LLM.
        Args:
            previous_responses (List[MessageThreadDTO]): The previous conversation turns.
        Returns:
            List[ConversationTurn]: The formatted conversation turns.
        """
        conversation_turns: List[ConversationTurn] = []
        last_tool_use_request: bool = False
        for message in previous_responses:
            if last_tool_use_request and not (
                message.actor == MessageThreadActor.USER and message.message_type == MessageType.TOOL_RESPONSE
            ):
                # remove the tool use request if the user has not responded to it
                conversation_turns.pop()
                last_tool_use_request = False
            role = ConversationRole.USER if message.actor == MessageThreadActor.USER else ConversationRole.ASSISTANT
            content: List[Dict[str, Any]] = []
            # sort message datas, keep text block first and tool use request last
            message_datas = list(message.message_data)
            for message_data in message_datas:
                content_data = message_data.content
                if isinstance(content_data, ExtendedThinkingContent):
                    if content_data.type == "thinking":
                        content.append(
                            {"type": "thinking", "thinking": content_data.thinking, "signature": content_data.signature}
                        )
                    else:
                        content.append(
                            {
                                "type": "redacted_thinking",
                                "data": content_data.thinking,
                            }
                        )
                elif isinstance(content_data, TextBlockContent):
                    content.append(
                        {
                            "type": "text",
                            "text": content_data.text,
                        }
                    )
                    last_tool_use_request = False
                elif isinstance(content_data, ToolUseResponseContent):
                    if (
                        last_tool_use_request
                        and conversation_turns
                        and not isinstance(conversation_turns[-1].content, str)
                        and conversation_turns[-1].content[-1].get("id") == content_data.tool_use_id
                    ):
                        content.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": content_data.tool_use_id,
                                "content": json.dumps(content_data.response),
                            }
                        )
                        last_tool_use_request = False
                elif isinstance(content_data, ToolUseRequestContent):
                    content.append(
                        {
                            "type": "tool_use",
                            "name": content_data.tool_name,
                            "id": content_data.tool_use_id,
                            "input": content_data.tool_input,
                        }
                    )
                    last_tool_use_request = True

                # handle file attachments
                else:
                    attachment_id = content_data.attachment_id
                    attachment_data = await attachment_data_task_map[attachment_id]
                    if attachment_data.attachment_metadata.file_type.startswith("image/"):
                        content.append(
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": attachment_data.attachment_metadata.file_type,
                                    "data": FileProcessor.get_base64_file_content(attachment_data.object_bytes),
                                },
                            }
                        )
                    last_tool_use_request = False

            content = [block for block in content if block["type"] != "text" or block["text"].strip()]
            if content:
                conversation_turns.append(ConversationTurn(role=role, content=content))

        return conversation_turns

    async def build_llm_payload(
        self,
        llm_model: LLModels,
        attachment_data_task_map: Dict[int, asyncio.Task[ChatAttachmentDataWithObjectBytes]],
        prompt: Optional[UserAndSystemMessages] = None,
        attachments: List[Attachment] = [],
        tool_use_response: Optional[ToolUseResponseData] = None,
        previous_responses: List[MessageThreadDTO] = [],
        tools: Optional[List[ConversationTool]] = None,
        tool_choice: Literal["none", "auto", "required"] = "auto",
        feedback: Optional[str] = None,
        cache_config: PromptCacheConfig = PromptCacheConfig(tools=False, system_message=False, conversation=False),
        search_web: bool = False,
    ) -> Dict[str, Any]:
        model_config = self._get_model_config(llm_model)
        # create conversation array
        messages: List[ConversationTurn] = await self.get_conversation_turns(
            previous_responses, attachment_data_task_map
        )

        # add system and user messages to conversation
        if prompt and prompt.user_message:
            user_message = ConversationTurn(
                role=ConversationRole.USER, content=[{"type": "text", "text": prompt.user_message}]
            )
            if attachments:
                for attachment in attachments:
                    attachment_data = await attachment_data_task_map[attachment.attachment_id]
                    if attachment_data.attachment_metadata.file_type.startswith("image/"):
                        # append at the beginning of the user message
                        user_message.content.insert(  # type: ignore
                            0,
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": attachment_data.attachment_metadata.file_type,
                                    "data": FileProcessor.get_base64_file_content(attachment_data.object_bytes),
                                },
                            },
                        )
            messages.append(user_message)

        # add tool result to conversation
        if tool_use_response:
            tool_message = ConversationTurn(
                role=ConversationRole.USER,
                content=[
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use_response.content.tool_use_id,
                        "content": json.dumps(tool_use_response.content.response),
                    }
                ],
            )
            messages.append(tool_message)
        if feedback:
            feedback_message = ConversationTurn(
                role=ConversationRole.USER, content=[{"type": "text", "text": feedback}]
            )
            messages.append(feedback_message)

        # create tools sorted by name
        tools = sorted(tools, key=lambda x: x.name) if tools else []

        # create body
        llm_payload: Dict[str, Any] = {
            "anthropic_version": model_config["VERSION"],
            "max_tokens": model_config["MAX_TOKENS"],
            "system": prompt.system_message if prompt and prompt.system_message else "",
            "messages": [message.model_dump(mode="json") for message in messages],
            "tools": [tool.model_dump(mode="json", by_alias=True, exclude_defaults=True) for tool in tools],
        }

        if model_config.get("THINKING") and model_config["THINKING"]["ENABLED"]:
            llm_payload["thinking"] = {"type": "enabled", "budget_tokens": model_config["THINKING"]["BUDGET_TOKENS"]}
        if cache_config.tools and tools and model_config["PROMPT_CACHING_SUPPORTED"]:
            llm_payload["tools"][-1]["cache_control"] = {"type": "ephemeral"}

        if (
            cache_config.system_message
            and prompt
            and prompt.system_message
            and model_config["PROMPT_CACHING_SUPPORTED"]
        ):
            llm_payload["system"] = [
                {
                    "type": "text",
                    "text": prompt.system_message,
                    "cache_control": {"type": "ephemeral"},
                }
            ]

        # Todo Uncomment this later when bedrock provide support of prompt caching

        if cache_config.conversation and messages and model_config["PROMPT_CACHING_SUPPORTED"]:
            for idx in range(min(2, len(llm_payload["messages"]))):
                llm_payload["messages"][idx]["content"][-1]["cache_control"] = {"type": "ephemeral"}

        return llm_payload

    async def _get_service_client(self):
        if not self.anthropic_client:
            self.anthropic_client = BedrockServiceClient()
        return self.anthropic_client

    async def _parse_non_streaming_response(self, response: InvokeModelResponseTypeDef) -> NonStreamingResponse:
        body: bytes = await response["body"].read()  # type: ignore
        llm_response = json.loads(body.decode("utf-8"))  # type: ignore

        # validate content array once we have the response

        content_array: List[Dict[str, Any]] = llm_response["content"]

        non_streaming_content_blocks: List[ResponseData] = []
        for content_block in content_array:
            if content_block["type"] == AnthropicResponseTypes.TEXT.value:
                non_streaming_content_blocks.append(
                    TextBlockData(
                        type=ContentBlockCategory.TEXT_BLOCK,
                        content=TextBlockContent(text=content_block["text"]),
                    )
                )
            elif content_block["type"] == AnthropicResponseTypes.TOOL_USE.value:
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
            usage=LLMUsage(
                input=llm_response["usage"]["input_tokens"],
                output=llm_response["usage"]["output_tokens"],
                cache_read=llm_response["usage"].get("cache_read_input_tokens"),
                cache_write=llm_response["usage"].get("cache_creation_input_tokens"),
            ),
            type=LLMCallResponseTypes.NON_STREAMING,
        )

    def _get_parsed_stream_event(
        self,
        event: Dict[str, Any],
        current_content_block_delta: str,
        current_running_block_type: Optional[ContentBlockCategory] = None,
    ) -> Tuple[List[StreamingEvent], Optional[ContentBlockCategory], Optional[str], Optional[LLMUsage]]:
        """
        Parses the streaming event and returns the corresponding content block and usage.

        Args:
            event (Dict[str, Any]): The event to parse.
            current_running_block_type (ContentBlockCategory): The current running block type.

        Returns:
            Tuple[Optional[StreamingContentBlock], Optional[LLMUsage]]: The content block and usage.
        """
        usage = LLMUsage(input=0, output=0, cache_read=0, cache_write=0)
        print(event)

        if event["type"] == "message_stop":
            invocation_metrics = event["amazon-bedrock-invocationMetrics"]
            if "inputTokenCount" in invocation_metrics:
                usage.input = invocation_metrics.get("inputTokenCount")
            if "outputTokenCount" in invocation_metrics:
                usage.output = invocation_metrics.get("outputTokenCount")

            return [], None, None, usage

        if event["type"] == "content_block_start" and event["content_block"]["type"] == "thinking":
            return ExtendedThinkingBlockStart(), ContentBlockCategory.EXTENDED_THINKING, None

        if event["type"] == "content_block_start" and event["content_block"]["type"] == "redacted_thinking":
            return RedactedThinking(data=event["content_block"]["data"]), ContentBlockCategory.EXTENDED_THINKING, None

        if event["type"] == "content_block_delta" and event["delta"]["type"] == "thinking_delta":
            return (
                [
                    ExtendedThinkingBlockDelta(
                        content=ExtendedThinkingBlockDeltaContent(thinking_delta=event["delta"]["thinking"])
                    )
                ],
                ContentBlockCategory.EXTENDED_THINKING,
                None,
                None,
            )

        if event["type"] == "content_block_delta" and event["delta"]["type"] == "signature_delta":
            return (
                [
                    ExtendedThinkingBlockEnd(
                        content=ExtendedThinkingBlockEndContent(signature=event["delta"]["signature"])
                    )
                ],
                ContentBlockCategory.EXTENDED_THINKING,
                None,
                None,
            )

        # parsers for tool use request blocks
        if event["type"] == "content_block_start" and event["content_block"]["type"] == "tool_use":
            return (
                [
                    ToolUseRequestStart(
                        type=StreamingEventType.TOOL_USE_REQUEST_START,
                        content=ToolUseRequestStartContent(
                            tool_name=event["content_block"]["name"],
                            tool_use_id=event["content_block"]["id"],
                        ),
                    )
                ],
                ContentBlockCategory.TOOL_USE_REQUEST,
                None,
                None,
            )

        if event["type"] == "content_block_delta" and event["delta"]["type"] == "input_json_delta":
            current_content_block_delta += event["delta"]["partial_json"]
            return (
                [
                    ToolUseRequestDelta(
                        type=StreamingEventType.TOOL_USE_REQUEST_DELTA,
                        content=ToolUseRequestDeltaContent(
                            input_params_json_delta=event["delta"]["partial_json"],
                        ),
                    )
                ],
                ContentBlockCategory.TOOL_USE_REQUEST,
                current_content_block_delta,
                None,
            )

        if (
            event["type"] == "content_block_stop"
            and current_running_block_type == ContentBlockCategory.TOOL_USE_REQUEST
        ):
            events_to_return: List[StreamingEvent] = []
            # claude does not return the final delta for tool use request in case of no params, so we need to add an empty delta
            if not current_content_block_delta:
                events_to_return.append(
                    ToolUseRequestDelta(
                        type=StreamingEventType.TOOL_USE_REQUEST_DELTA,
                        content=ToolUseRequestDeltaContent(
                            input_params_json_delta="{}",
                        ),
                    )
                )

            events_to_return.append(
                ToolUseRequestEnd(
                    type=StreamingEventType.TOOL_USE_REQUEST_END,
                )
            )

            current_content_block_delta = ""

            return (
                events_to_return,
                ContentBlockCategory.TOOL_USE_REQUEST,
                current_content_block_delta,
                None,
            )

        # parsers for text blocks
        if event["type"] == "content_block_start" and event["content_block"]["type"] == "text":
            return (
                [
                    TextBlockStart(
                        type=StreamingEventType.TEXT_BLOCK_START,
                    )
                ],
                ContentBlockCategory.TEXT_BLOCK,
                None,
                None,
            )

        if event["type"] == "content_block_delta" and event["delta"]["type"] == "text_delta":
            return (
                [
                    TextBlockDelta(
                        type=StreamingEventType.TEXT_BLOCK_DELTA,
                        content=TextBlockDeltaContent(
                            text=event["delta"]["text"],
                        ),
                    )
                ],
                ContentBlockCategory.TEXT_BLOCK,
                None,
                None,
            )

        if event["type"] == "content_block_stop" and current_running_block_type == ContentBlockCategory.TEXT_BLOCK:
            return (
                [
                    TextBlockEnd(
                        type=StreamingEventType.TEXT_BLOCK_END,
                    )
                ],
                ContentBlockCategory.TEXT_BLOCK,
                None,
                None,
            )

        return [], None, None, None

    async def _parse_streaming_response(
        self,
        response: InvokeModelWithResponseStreamResponseTypeDef,
        async_bedrock_client: BedrockRuntimeClient,
        model_config: Dict[str, Any],
    ) -> StreamingResponse:
        usage = LLMUsage(input=0, output=0, cache_read=0, cache_write=0)
        streaming_completed: bool = False
        accumulated_events: List[StreamingEvent] = []

        async def stream_content() -> AsyncIterator[StreamingEvent]:
            nonlocal usage
            nonlocal streaming_completed
            nonlocal accumulated_events
            non_combinable_events = [
                RedactedThinking,
                TextBlockStart,
                TextBlockEnd,
                ToolUseRequestStart,
                ToolUseRequestEnd,
                ExtendedThinkingBlockStart,
                ExtendedThinkingBlockEnd,
            ]
            buffer: List[StreamingEvent] = []
            current_type: Optional[type] = None
            current_running_block_type: Optional[ContentBlockCategory] = None
            current_content_block_delta: str = ""
            response_body = cast(AsyncIterable[Dict[str, Any]], response["body"])
            async for event in response_body:
                chunk = json.loads(event["chunk"]["bytes"])
                # yield content block delta
                try:
                    event_blocks, event_block_category, content_block_delta, event_usage = (
                        self._get_parsed_stream_event(chunk, current_content_block_delta, current_running_block_type)
                    )
                    if event_usage:
                        usage += event_usage

                    for event_block in event_blocks:
                        last_block_type = type(event_block)
                        if current_type is None:
                            current_type = last_block_type
                        if buffer and (
                            current_type in non_combinable_events
                            or last_block_type != current_type
                            or len(buffer) == (model_config.get("STREAM_BATCH_SIZE") or 1)
                        ):
                            combined_event = sum(buffer[1:], start=buffer[0])
                            yield combined_event
                            buffer.clear()
                            current_type = last_block_type

                        buffer.append(event_block)

                    if event_blocks:
                        current_running_block_type = event_block_category
                        accumulated_events.extend(event_blocks)

                    if content_block_delta is not None:
                        current_content_block_delta = content_block_delta
                except Exception:
                    # gracefully handle new events. See Anthropic docs here - https://docs.anthropic.com/en/api/messages-streaming#other-events
                    pass
            if buffer:
                combined_event = sum(buffer[1:], start=buffer[0])
                yield combined_event

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

        # close the async bedrock client
        async def close_client():
            nonlocal streaming_completed
            while not streaming_completed:
                await asyncio.sleep(0.1)
            await async_bedrock_client.__aexit__(None, None, None)

        asyncio.create_task(close_client())

        return StreamingResponse(
            content=stream_content(),
            usage=asyncio.create_task(get_usage()),
            type=LLMCallResponseTypes.STREAMING,
            accumulated_events=asyncio.create_task(get_accumulated_events()),
        )

    async def call_service_client(
        self, llm_payload: Dict[str, Any], model: LLModels, stream: bool = False, response_type: Optional[str] = None
    ) -> UnparsedLLMCallResponse:
        anthropic_client = await self._get_service_client()
        AppLogger.log_debug(json.dumps(llm_payload))
        model_config = self._get_model_config(model)
        if stream is False:
            response = await anthropic_client.get_llm_non_stream_response(
                llm_payload=llm_payload, model=model_config["NAME"]
            )
            return await self._parse_non_streaming_response(response)
        else:
            response, async_bedrock_client = await anthropic_client.get_llm_stream_response(
                llm_payload=llm_payload, model=model_config["NAME"]
            )
            return await self._parse_streaming_response(response, async_bedrock_client, model_config)
