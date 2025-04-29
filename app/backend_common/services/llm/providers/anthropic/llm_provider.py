import asyncio
import json
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple

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
    AnthropicResponseTypes,
)


class Anthropic(BaseLLMProvider):
    def __init__(self):
        super().__init__(LLMProviders.ANTHROPIC.value)
        self.anthropic_client = None

    def get_conversation_turns(self, previous_responses: List[MessageThreadDTO]) -> List[ConversationTurn]:
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
            message_datas.sort(key=lambda x: 0 if isinstance(x, TextBlockData) else 1)
            for message_data in message_datas:
                content_data = message_data.content
                if isinstance(content_data, TextBlockContent):
                    content.append(
                        {
                            "text": content_data.text,
                        }
                    )
                    last_tool_use_request = False
                elif isinstance(content_data, ToolUseResponseContent):
                    if (
                        last_tool_use_request
                        and conversation_turns
                        and not isinstance(conversation_turns[-1].content, str)
                        and conversation_turns[-1].content[-1]["toolUse"]["toolUseId"] == content_data.tool_use_id
                    ):
                        content.append({
                            "toolResult":
                                {
                                    "toolUseId": content_data.tool_use_id,
                                    "content": [{"json": content_data.response}],
                                }
                            }
                        )
                        last_tool_use_request = False
                else:
                    content.append(
                        {
                            "toolUse": {
                                "name": content_data.tool_name,
                                "toolUseId": content_data.tool_use_id,
                                "input": content_data.tool_input,
                            }
                        }
                    )
                    last_tool_use_request = True
            if content:
                conversation_turns.append(ConversationTurn(role=role, content=content))

        return conversation_turns

    def build_llm_payload(
        self,
        llm_model,
        prompt: Optional[UserAndSystemMessages] = None,
        tool_use_response: Optional[ToolUseResponseData] = None,
        previous_responses: List[MessageThreadDTO] = [],
        tools: Optional[List[ConversationTool]] = None,
        cache_config: PromptCacheConfig = PromptCacheConfig(tools=False, system_message=False, conversation=False),
        use_converse=False
    ) -> Dict[str, Any]:

        if use_converse:
            return self.build_llm_payload_converse(
                llm_model,
                prompt,
                tool_use_response,
                previous_responses,
                tools,
                cache_config,
            )

        model_config = self._get_model_config(llm_model)
        # create conversation array
        messages: List[ConversationTurn] = self.get_conversation_turns(previous_responses)

        # add system and user messages to conversation
        if prompt:
            user_message = ConversationTurn(
                role=ConversationRole.USER, content=[{"type": "text", "text": prompt.user_message}]
            )
            messages.append(user_message)

        # add tool result to conversation
        if tool_use_response:
            tool_message = ConversationTurn(
                role=ConversationRole.USER,
                content=[{
                    "toolResult": {
                        "toolUseId": tool_use_response.content.tool_use_id,
                        "content": json.dumps(tool_use_response.content.response),
                    }
                    }
                ],
            )
            messages.append(tool_message)
        # create tools sorted by name
        tools = sorted(tools, key=lambda x: x.name) if tools else []

        # create body
        llm_payload: Dict[str, Any] = {
            "anthropic_version": model_config["VERSION"],
            "max_tokens": model_config["MAX_TOKENS"],
            "system": prompt.system_message if prompt else "",
            "messages": [message.model_dump(mode="json") for message in messages],
            "tools": [tool.model_dump(mode="json") for tool in tools],
        }

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

        if cache_config.conversation and messages and model_config["PROMPT_CACHING_SUPPORTED"]:
            llm_payload["messages"][-1]["content"][-1]["cache_control"] = {"type": "ephemeral"}

        return llm_payload

    def format_tools(self, tools: Optional[List[ConversationTool]]):
        formatted_tools = []
        for tool in tools:
            formatted_tools.append({
                "toolSpec": {
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": {
                        "json": tool.input_schema
                    }
                }
            })
        return formatted_tools


    def build_llm_payload_converse(
        self,
        llm_model,
        prompt: Optional[UserAndSystemMessages] = None,
        tool_use_response: Optional[ToolUseResponseData] = None,
        previous_responses: List[MessageThreadDTO] = [],
        tools: Optional[List[ConversationTool]] = None,
        cache_config: PromptCacheConfig = PromptCacheConfig(tools=False, system_message=False, conversation=False),
    ) -> Dict[str, Any]:

        model_config = self._get_model_config(llm_model)
        # create conversation array
        messages: List[ConversationTurn] = self.get_conversation_turns(previous_responses)

        # add system and user messages to conversation
        if prompt:
            user_message = ConversationTurn(
                role=ConversationRole.USER, content=[{"text": prompt.user_message}]
            )
            messages.append(user_message)

        # add tool result to conversation
        if tool_use_response:
            tool_message = ConversationTurn(
                role=ConversationRole.USER,
                content = [{
                    "toolResult":
                        {
                            "toolUseId": tool_use_response.content.tool_use_id,
                            "content": [{"json": tool_use_response.content.response}],
                        }
                }
                ],
            )
            messages.append(tool_message)

        # create tools sorted by name
        tools = sorted(tools, key=lambda x: x.name) if tools else []
        tools = self.format_tools(tools)
        # create body
        llm_payload: Dict[str, Any] = {
            "anthropic_version": model_config["VERSION"],
            "max_tokens": model_config["MAX_TOKENS"],
            "system": prompt.system_message if prompt else "",
            "messages": [message.model_dump(mode="json") for message in messages],
            "toolConfig": {
                "tools": tools
            },
        }

        if cache_config.tools and tools and model_config["PROMPT_CACHING_SUPPORTED"]:
            llm_payload["toolConfig"]["tools"].append({
                                "cachePoint": {
                                    "type": "default"
                                }
                            })
        if (
            cache_config.system_message
            and prompt
            and prompt.system_message
            and model_config["PROMPT_CACHING_SUPPORTED"]
        ):
            llm_payload["system"] = [
                {
                    "text": prompt.system_message,
                },
                {
                    "cachePoint": {"type": "default"},
                }
            ]

        if cache_config.conversation and messages and model_config["PROMPT_CACHING_SUPPORTED"]:
            llm_payload["messages"][-1]["content"].append({
                    "cachePoint": {"type": "default"},
                })

        # print("llm message", llm_payload["messages"])
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
            usage=LLMUsage(input=llm_response["usage"]["input_tokens"], output=llm_response["usage"]["output_tokens"]),
            type=LLMCallResponseTypes.NON_STREAMING,
        )

    def _get_parsed_stream_event(
            self, event: Dict[str, Any], current_running_block_type: Optional[ContentBlockCategory] = None
    ) -> Tuple[Optional[StreamingEvent], Optional[ContentBlockCategory], Optional[LLMUsage]]:
        usage = LLMUsage(input=0, output=0, cache_read=0, cache_write=0)

        # Handle messageStop event
        if "messageStop" in event:
            return None, None, usage

        # Handle contentBlockDelta
        if "contentBlockDelta" in event:
            delta = event["contentBlockDelta"]["delta"]

            if "text" in delta and not (current_running_block_type and current_running_block_type != ContentBlockCategory.TEXT_BLOCK):
                delta_text = delta.get("text", "").strip() or "empty"
                return (
                    TextBlockDelta(
                        type=StreamingEventType.TEXT_BLOCK_DELTA,
                        content=TextBlockDeltaContent(text=delta_text),
                    ),
                    ContentBlockCategory.TEXT_BLOCK,
                    None,
                )

            if "toolUse" in delta and current_running_block_type == ContentBlockCategory.TOOL_USE_REQUEST:
                tool_use_delta = delta.get("toolUse", {})
                return (
                    ToolUseRequestDelta(
                        type=StreamingEventType.TOOL_USE_REQUEST_DELTA,
                        content=ToolUseRequestDeltaContent(
                            input_params_json_delta=tool_use_delta.get("input", ""),
                        ),
                    ),
                    ContentBlockCategory.TOOL_USE_REQUEST,
                    None,
                )

        # Handle contentBlockStart
        if "contentBlockStart" in event:
            start = event["contentBlockStart"]["start"]
            if "toolUse" in start:
                tool_use = start["toolUse"]
                return (
                    ToolUseRequestStart(
                        type=StreamingEventType.TOOL_USE_REQUEST_START,
                        content=ToolUseRequestStartContent(
                            tool_name=tool_use.get("name", ""),
                            tool_use_id=tool_use.get("toolUseId", ""),
                        ),
                    ),
                    ContentBlockCategory.TOOL_USE_REQUEST,
                    None,
                )
            else:
                # Assume it’s starting a text block
                return (
                    TextBlockStart(
                        type=StreamingEventType.TEXT_BLOCK_START,
                    ),
                    ContentBlockCategory.TEXT_BLOCK,
                    None,
                )

        # Handle contentBlockStop
        if "contentBlockStop" in event:
            if current_running_block_type == ContentBlockCategory.TEXT_BLOCK:
                return (
                    TextBlockEnd(
                        type=StreamingEventType.TEXT_BLOCK_END,
                    ),
                    None,
                    None,
                )
            elif current_running_block_type == ContentBlockCategory.TOOL_USE_REQUEST:
                return (
                    ToolUseRequestEnd(
                        type=StreamingEventType.TOOL_USE_REQUEST_END,
                    ),
                    None,
                    None,
                )

        # Handle metadata event
        if "metadata" in event:
            usage_data = event["metadata"].get("usage", {})
            usage.input = usage_data.get("inputTokens", 0)
            usage.output = usage_data.get("outputTokens", 0)
            usage.cache_read = usage_data.get("cacheReadInputTokens", 0)
            usage.cache_write = usage_data.get("cacheWriteInputTokens", 0)
            return None, current_running_block_type, usage

        # Unrecognized event
        return None, current_running_block_type, None

    async def _parse_streaming_response(
            self, response: Any, async_bedrock_client: BedrockRuntimeClient
    ) -> StreamingResponse:
        usage = LLMUsage(input=0, output=0, cache_read=0, cache_write=0)
        streaming_completed: bool = False
        accumulated_events: List[StreamingEvent] = []

        async def stream_content() -> AsyncIterator[StreamingEvent]:
            nonlocal usage
            nonlocal streaming_completed
            nonlocal accumulated_events
            current_running_block_type: Optional[ContentBlockCategory] = None

            async for event in response["stream"]:
                try:
                    # Directly use the parsed event dictionary
                    event_block, event_block_category, event_usage = self._get_parsed_stream_event(
                        event, current_running_block_type
                    )

                    if event_usage:
                        usage += event_usage

                    if event_block:
                        if event_block_category is not None:
                            current_running_block_type = event_block_category
                        accumulated_events.append(event_block)
                        yield event_block

                    # print("event meta data", event.get("metadata"))
                    # Handle usage metrics if provided separately
                    if "metadata" in event and "usage" in event["metadata"]:
                        usage.input = event["metadata"]["usage"].get("inputTokens", usage.input)
                        usage.output = event["metadata"]["usage"].get("outputTokens", usage.output)
                        usage.cache_read = event["metadata"]["usage"].get("cacheReadInputTokens", usage.cache_read)
                        usage.cache_write = event["metadata"]["usage"].get("cacheWriteInputTokens", usage.cache_write)

                    # Handle end of streaming
                    if "messageStop" in event:
                        streaming_completed = True

                except Exception as e:
                    print(f"Error processing streaming event: {e}")
                    pass

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
            # data = []
            # async for chunk in response["stream"]:
            #     data.append(chunk)

            return await self._parse_streaming_response(response, async_bedrock_client)
