import asyncio
import json
import uuid
from typing import Any, AsyncIterator, Dict, List, Literal, Optional, Tuple, Type

from deputydev_core.services.tiktoken import TikToken
from deputydev_core.utils.app_logger import AppLogger
from openai.types import responses
from openai.types.responses import Response
from openai.types.responses.response_stream_event import ResponseStreamEvent
from pydantic import BaseModel

from app.backend_common.caches.code_gen_tasks_cache import (
    CodeGenTasksCache,
)
from app.backend_common.constants.constants import LLMProviders
from app.backend_common.models.dto.message_thread_dto import (
    ContentBlockCategory,
    ExtendedThinkingContent,
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
from app.backend_common.service_clients.openai.openai import OpenAIServiceClient
from app.backend_common.services.chat_file_upload.file_processor import FileProcessor
from app.backend_common.services.llm.base_llm_provider import BaseLLMProvider
from app.backend_common.services.llm.dataclasses.main import (
    ChatAttachmentDataWithObjectBytes,
    ConversationRole,
    ConversationTool,
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
from app.main.blueprints.one_dev.services.query_solver.dataclasses.main import Attachment
from app.main.blueprints.one_dev.utils.cancellation_checker import (
    CancellationChecker,
)


class OpenRouter(BaseLLMProvider):
    def __init__(self, checker: Optional[CancellationChecker] = None) -> None:
        super().__init__(LLMProviders.OPENAI.value, checker=checker)
        self._active_streams: Dict[str, AsyncIterator] = {}
        self.anthropic_client = None

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
        disable_caching: bool = False,
    ) -> Dict[str, Any]:
        """
        Formats the conversation for OpenRouter's GPT model.

        Args:
            prompt (Dict[str, str]): A prompt object.
            previous_responses (List[Dict[str, str]] ): previous messages to pass to LLM

        Returns:
            List[Dict[str, str]]: A formatted list of message dictionaries.
        """
        model_config = self._get_model_config(llm_model)
        formatted_tools = []
        messages = []
        if tools:
            for tool in tools:
                tool = responses.FunctionToolParam(
                    name=tool.name,
                    parameters=tool.input_schema.model_dump(mode="json", exclude_unset=True, by_alias=True)
                    if tool.input_schema.properties
                    else None,
                    description=tool.description,
                    type="function",
                    strict=False,
                )
                formatted_tools.append(tool)

            formatted_tools = sorted(formatted_tools, key=lambda x: x["name"])
            tool_choice = tool_choice if tool_choice else "auto"

        if previous_responses:
            messages = await self.get_conversation_turns(previous_responses, attachment_data_task_map)

        if prompt and prompt.user_message:
            user_message = {"role": "user", "content": [{"type": "input_text", "text": prompt.user_message}]}
            if attachments:
                for attachment in attachments:
                    if attachment.attachment_id not in attachment_data_task_map:
                        continue
                    attachment_data = await attachment_data_task_map[attachment.attachment_id]
                    if attachment_data.attachment_metadata.file_type.startswith("image/"):
                        user_message["content"].append(
                            {
                                "type": "input_image",
                                "image_url": f"data:{attachment_data.attachment_metadata.file_type};base64,{FileProcessor.get_base64_file_content(attachment_data.object_bytes)}",
                            }
                        )
            messages.append(user_message)

        if tool_use_response:
            tool_response = {
                "type": "function_call_output",
                "call_id": tool_use_response.content.tool_use_id,
                "output": json.dumps(tool_use_response.content.response),
            }
            messages.append(tool_response)

        return {
            "max_tokens": model_config["MAX_TOKENS"],
            "system_message": prompt.system_message if prompt and prompt.system_message else "",
            "conversation_messages": messages,
            "tools": formatted_tools,
            "tool_choice": tool_choice,
        }

    async def get_conversation_turns(  # noqa: C901
        self,
        previous_responses: List[MessageThreadDTO],
        attachment_data_task_map: Dict[int, asyncio.Task[ChatAttachmentDataWithObjectBytes]],
    ) -> List[Dict[str, Any]]:
        """
        Formats the conversation as required by the specific LLM.
        Args:
            previous_responses (List[MessageThreadDTO]): The previous conversation turns.
        Returns:
            List[ConversationTurn]: The formatted conversation turns.
        """
        conversation_turns: List[Dict[str, Any]] = []
        tool_requests: Dict[str, Dict[str, Any]] = {}
        tool_requests_order: List[str] = []
        for message in previous_responses:
            role = ConversationRole.USER if message.actor == MessageThreadActor.USER else ConversationRole.ASSISTANT
            message_datas = list(message.message_data)
            for message_data in message_datas:
                content_data = message_data.content
                if isinstance(content_data, TextBlockContent):
                    conversation_turns.append({"role": role.value, "content": content_data.text})
                elif isinstance(content_data, ToolUseResponseContent):
                    while len(tool_requests_order) > 0:
                        if tool_requests_order[0] == content_data.tool_use_id:
                            conversation_turns.append(tool_requests[content_data.tool_use_id])
                            conversation_turns.append(
                                {
                                    "call_id": content_data.tool_use_id,
                                    "output": json.dumps(content_data.response),
                                    "type": "function_call_output",
                                }
                            )
                            tool_requests_order.pop(0)
                            break
                        tool_requests_order.pop(0)
                elif isinstance(content_data, ToolUseRequestContent):
                    tool_requests[content_data.tool_use_id] = {
                        "call_id": content_data.tool_use_id,
                        "arguments": json.dumps(content_data.tool_input),
                        "name": content_data.tool_name,
                        "type": "function_call",
                    }
                    tool_requests_order.append(content_data.tool_use_id)
                elif isinstance(content_data, ExtendedThinkingContent):
                    continue

                else:
                    attachment_id = content_data.attachment_id
                    if attachment_id not in attachment_data_task_map:
                        continue
                    attachment_data = await attachment_data_task_map[attachment_id]
                    if attachment_data.attachment_metadata.file_type.startswith("image/"):
                        conversation_turns.append(
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "input_image",
                                        "image_url": f"data:{attachment_data.attachment_metadata.file_type};base64,{FileProcessor.get_base64_file_content(attachment_data.object_bytes)}",
                                    }
                                ],
                            }
                        )
        return conversation_turns

    def _parse_non_streaming_response(self, response: Response) -> NonStreamingResponse:
        """
        Parses the response from OpenRouter's GPT model.

        Args:
            response : The raw response from the GPT model.

        Returns:
            NonStreamingResponse: Parsed response
        """
        non_streaming_content_blocks: List[ResponseData] = []
        for block in response.output:
            if block.type == "message":
                non_streaming_content_blocks.append(TextBlockData(content=TextBlockContent(text=response.output_text)))
            if block.type == "function_call":
                non_streaming_content_blocks.append(
                    ToolUseRequestData(
                        content=ToolUseRequestContent(
                            tool_input=json.loads(block.arguments),
                            tool_name=block.name,
                            tool_use_id=block.call_id,
                        )
                    )
                )

        return NonStreamingResponse(
            content=non_streaming_content_blocks,
            usage=(
                LLMUsage(
                    input=response.usage.input_tokens - response.usage.input_tokens_details.cached_tokens,
                    output=response.usage.output_tokens,
                    cache_read=response.usage.input_tokens_details.cached_tokens,
                )
                if response.usage
                else LLMUsage(input=0, output=0)
            ),
        )

    def _parse_non_streaming_response_new(self, response: Response) -> NonStreamingResponse:
        """
        Parses the response from GPT or similar LLM models into your internal schema.
        """
        non_streaming_content_blocks: List[ResponseData] = []

        for block in response.output:
            if block.type == "message":
                for content_piece in getattr(block, "content", []):
                    if getattr(content_piece, "type", None) == "output_text":
                        non_streaming_content_blocks.append(
                            TextBlockData(content=TextBlockContent(text=content_piece.text))
                        )
            elif block.type == "function_call":
                # Prefer parsed_arguments if available
                if getattr(block, "parsed_arguments", None) is not None:
                    tool_input = block.parsed_arguments
                    # If it's a pydantic object, convert to dict
                    if hasattr(tool_input, "model_dump"):
                        tool_input = tool_input.model_dump()
                    elif hasattr(tool_input, "dict"):  # For older pydantic
                        tool_input = tool_input.dict()
                else:
                    tool_input = json.loads(block.arguments)
                non_streaming_content_blocks.append(
                    ToolUseRequestData(
                        content=ToolUseRequestContent(
                            tool_input=tool_input,
                            tool_name=block.name,
                            tool_use_id=block.call_id,
                        )
                    )
                )
            # All other block types are silently skipped

        usage_obj = (
            LLMUsage(
                input=response.usage.input_tokens - getattr(response.usage.input_tokens_details, "cached_tokens", 0),
                output=response.usage.output_tokens,
                cache_read=getattr(response.usage.input_tokens_details, "cached_tokens", 0),
            )
            if getattr(response, "usage", None)
            else LLMUsage(input=0, output=0)
        )

        return NonStreamingResponse(
            content=non_streaming_content_blocks,
            usage=usage_obj,
        )

    async def call_service_client(
        self,
        session_id: int,
        llm_payload: Dict[str, Any],
        model: LLModels,
        stream: bool = False,
        response_type: Optional[Literal["text", "json_object", "json_schema"]] = None,
        parallel_tool_calls: bool = True,
        text_format: Optional[Type[BaseModel]] = None,
    ) -> UnparsedLLMCallResponse:
        """
        Calls the OpenRouter service client.

        Args:
            messages (List[Dict[str, str]]): Formatted conversation messages.

        Returns:
            str: The response from the GPT model.
        """
        if not response_type:
            response_type = "text"
        model_config = self._get_model_config(model)
        stream_id = str(uuid.uuid4())
        if stream:
            response = await OpenAIServiceClient().get_llm_stream_response(
                conversation_messages=llm_payload["conversation_messages"],
                model=model_config["NAME"],
                response_type=response_type,
                tools=llm_payload["tools"],
                instructions=llm_payload["system_message"],
                tool_choice="auto",
                max_output_tokens=model_config["MAX_TOKENS"],
                parallel_tool_calls=parallel_tool_calls,
            )
            return await self._parse_streaming_response(response, stream_id, session_id)
        if response_type == "text":
            response = await OpenAIServiceClient().get_llm_non_stream_response_api(
                conversation_messages=llm_payload["conversation_messages"],
                model=model_config["NAME"],
                tool_choice=llm_payload["tool_choice"],
                tools=llm_payload["tools"],
                instructions=llm_payload["system_message"],
                max_output_tokens=model_config["MAX_TOKENS"],
                parallel_tool_calls=parallel_tool_calls,
                text_format=text_format,
            )
            return self._parse_non_streaming_response_new(response)
        else:
            response = await OpenAIServiceClient().get_llm_non_stream_response(
                conversation_messages=llm_payload["conversation_messages"],
                model=model_config["NAME"],
                response_type=response_type,
                tools=llm_payload["tools"],
                instructions=llm_payload["system_message"],
                tool_choice=llm_payload["tool_choice"],
                max_output_tokens=model_config["MAX_TOKENS"],
                parallel_tool_calls=parallel_tool_calls,
            )
            return self._parse_non_streaming_response(response)

    async def _parse_streaming_response(  # noqa: C901
        self, response: AsyncIterator[ResponseStreamEvent], stream_id: str = None, session_id: Optional[int] = None
    ) -> StreamingResponse:
        stream_id = stream_id or str(uuid.uuid4())
        usage = LLMUsage(input=0, output=0, cache_read=0, cache_write=None)

        streaming_completed = asyncio.Event()

        # Manual token counting for when final usage is not available

        accumulated_events = []

        async def stream_content() -> AsyncIterator[StreamingEvent]:
            nonlocal usage
            nonlocal streaming_completed
            nonlocal accumulated_events
            self._active_streams[stream_id] = response
            nonlocal session_id

            try:
                async for event in response:
                    # Check for task cancellation
                    if self.checker and self.checker.is_cancelled():
                        await CodeGenTasksCache.cleanup_session_data(session_id)
                        raise asyncio.CancelledError()
                    try:
                        event_block, _event_block_category, event_usage = await self._get_parsed_stream_event(event)
                        if event_usage:
                            usage += event_usage
                        if event_block:
                            accumulated_events.append(event_block)
                            yield event_block
                    except Exception:  # noqa: BLE001
                        # Depending on the error, you might want to break or continue
                        pass
            except Exception as e:  # noqa: BLE001
                AppLogger.log_error(f"Streaming Error in OpenRouter: {e}")
            finally:
                if self.checker:
                    await self.checker.stop_monitoring()
                streaming_completed.set()
                await close_client()

        async def close_client() -> None:
            nonlocal streaming_completed
            streaming_completed.set()
            if stream_id in self._active_streams:
                try:
                    stream_iter = self._active_streams.pop(stream_id)
                    await stream_iter.aclose()
                except Exception:  # noqa: BLE001
                    AppLogger.log_error("OpenRouter Cancel Error")
                if stream_id in self._active_streams:
                    del self._active_streams[stream_id]

        async def get_usage() -> LLMUsage:
            nonlocal usage
            nonlocal streaming_completed
            await streaming_completed.wait()
            return usage

        async def get_accumulated_events() -> List[StreamingEvent]:
            nonlocal accumulated_events
            nonlocal streaming_completed
            await streaming_completed.wait()
            return accumulated_events

        return StreamingResponse(
            content=stream_content(),
            usage=asyncio.create_task(get_usage()),
            type=LLMCallResponseTypes.STREAMING,
            accumulated_events=asyncio.create_task(get_accumulated_events()),
        )

    async def _get_parsed_stream_event(
        self, event: ResponseStreamEvent
    ) -> Tuple[Optional[StreamingEvent], Optional[ContentBlockCategory], Optional[LLMUsage]]:
        usage = LLMUsage(input=0, output=0, cache_read=0, cache_write=None)
        if event.type == "response.completed" and event.response.usage:
            usage.cache_read = event.response.usage.input_tokens_details.cached_tokens
            usage.input = event.response.usage.input_tokens - usage.cache_read
            usage.output = event.response.usage.output_tokens
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
                TextBlockStart(type=StreamingEventType.TEXT_BLOCK_START),
                ContentBlockCategory.TEXT_BLOCK,
                None,
            )
        if event.type == "response.output_text.delta":
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
        if event.type == "response.output_text.done":
            return (
                TextBlockEnd(
                    type=StreamingEventType.TEXT_BLOCK_END,
                ),
                ContentBlockCategory.TEXT_BLOCK,
                None,
            )

        return None, None, None

    async def get_tokens(self, content: str, model: LLModels) -> int:
        tiktoken_client = TikToken()
        token_count = tiktoken_client.count(text=content)

        return token_count
