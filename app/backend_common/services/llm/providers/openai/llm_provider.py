import asyncio
import json
from typing import Any, Dict, List, Optional, Literal, AsyncIterator
from openai.types.responses.response_stream_event import ResponseStreamEvent
from openai.types.chat import ChatCompletion
from openai.types import responses
from app.backend_common.services.llm.dataclasses.main import (
    ConversationRole,
    ConversationTurn,
    LLMCallResponseTypes,
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
    TextBlockStartContent,
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
    MessageThreadActor,
    MessageType,
    ToolUseResponseContent,
)
from app.backend_common.service_clients.openai.openai import OpenAIServiceClient
from app.backend_common.services.llm.base_llm_provider import BaseLLMProvider
from app.backend_common.services.llm.dataclasses.main import (
    ConversationTool,
    NonStreamingResponse,
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
        feedback: Optional[str] = None,
        cache_config=None,
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
        model_config = self._get_model_config(llm_model)
        formatted_tools = []
        messages = []
        for tool in tools:
            tool = responses.FunctionToolParam(
                name=tool.name,
                parameters=tool.input_schema,
                description=tool.description,
                type="function",
                strict=False,
            )
            formatted_tools.append(tool)
        formatted_tools = sorted(formatted_tools, key=lambda x: x["name"]) if tools else []

        if previous_responses:
            messages = self.get_conversation_turns(previous_responses)

        if prompt:
            user_message = {"role": "user", "content": prompt.user_message}
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
            "system_message": prompt.system_message if prompt else "",
            "conversation_messages": messages,
            "tools": formatted_tools,
        }

    def get_conversation_turns(self, previous_responses: List[MessageThreadDTO]) -> List[dict]:
        """
        Formats the conversation as required by the specific LLM.
        Args:
            previous_responses (List[MessageThreadDTO]): The previous conversation turns.
        Returns:
            List[ConversationTurn]: The formatted conversation turns.
        """
        conversation_turns = []
        last_tool_use_request: bool = False
        for message in previous_responses:
            if last_tool_use_request and not (
                message.actor == MessageThreadActor.USER and message.message_type == MessageType.TOOL_RESPONSE
            ):
                # remove the tool use request if the user has not responded to it
                conversation_turns.pop()
                last_tool_use_request = False
            role = ConversationRole.USER if message.actor == MessageThreadActor.USER else ConversationRole.ASSISTANT
            # sort message datas, keep text block first and tool use request last
            message_datas = list(message.message_data)
            message_datas.sort(key=lambda x: 0 if isinstance(x, TextBlockData) else 1)
            for message_data in message_datas:
                content_data = message_data.content
                if isinstance(content_data, TextBlockContent):
                    conversation_turns.append({"role": role.value, "content": content_data.text})
                    last_tool_use_request = False
                elif isinstance(content_data, ToolUseResponseContent):
                    if (
                        last_tool_use_request
                        and conversation_turns
                        and conversation_turns[-1].get("call_id") == content_data.tool_use_id
                    ):
                        conversation_turns.append(
                            {
                                "call_id": content_data.tool_use_id,
                                "output": json.dumps(content_data.response),
                                "type": "function_call_output",
                            }
                        )
                        last_tool_use_request = False
                else:
                    conversation_turns.append(
                        {
                            "call_id": content_data.tool_use_id,
                            "arguments": json.dumps(content_data.tool_input),
                            "name": content_data.tool_name,
                            "type": "function_call",
                        }
                    )
                    last_tool_use_request = True
        return conversation_turns

    def _parse_non_streaming_response(self, response: ChatCompletion) -> NonStreamingResponse:
        """
        Parses the response from OpenAI's GPT model.

        Args:
            response : The raw response from the GPT model.

        Returns:
            NonStreamingResponse: Parsed response
        """
        non_streaming_content_blocks: List[ResponseData] = []
        # response.choices[0].message.content = response.output_text
        # response.choices[0].message
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
                    input=response.usage.input_tokens,
                    output=response.usage.output_tokens,
                    cache_read=response.usage.input_tokens_details.cached_tokens,
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
                tools=llm_payload["tools"],
                instructions=llm_payload["system_message"],
                tool_choice="auto",
            )
            return await self._parse_streaming_response(response)
        else:
            response = await OpenAIServiceClient().get_llm_non_stream_response(
                conversation_messages=llm_payload["conversation_messages"],
                model=model_config["NAME"],
                response_type=response_type,
                tools=llm_payload["tools"],
                instructions=llm_payload["system_message"],
                tool_choice="auto",
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
