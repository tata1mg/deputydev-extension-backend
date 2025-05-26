import asyncio
import json
import uuid
from typing import Any, AsyncIterator, Dict, List, Literal, Optional, Tuple

from google.genai import types as google_genai_types
from torpedo.exceptions import BadRequestException

# Your existing DTOs and base class
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
from app.backend_common.service_clients.gemini.gemini import GeminiServiceClient
from app.backend_common.services.llm.base_llm_provider import BaseLLMProvider
from app.backend_common.services.llm.dataclasses.main import (
    ChatAttachmentDataWithObjectBytes,
    ConversationRoleGemini,
    ConversationTool,
    LLMCallResponseTypes,
    NonStreamingResponse,
    PromptCacheConfig,
    StreamingEvent,
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


class Google(BaseLLMProvider):
    def __init__(self):
        super().__init__(LLMProviders.GOOGLE.value)

    async def get_conversation_turns(
        self,
        previous_responses: List[MessageThreadDTO],
        attachment_data_task_map: Dict[int, asyncio.Task[ChatAttachmentDataWithObjectBytes]],
    ) -> List[google_genai_types.Content]:
        """
        Formats the conversation history for Google's Gemini model.

        Args:
            previous_responses (List[MessageThreadDTO]): The previous conversation turns.

        Returns:
            List[Content]: The formatted conversation history for Gemini.
        """
        conversation_turns: List[google_genai_types.Content] = []
        last_tool_use_request: bool = False

        for message in previous_responses:
            if last_tool_use_request and not (
                message.actor == MessageThreadActor.USER and message.message_type == MessageType.TOOL_RESPONSE
            ):
                # Remove the previous tool_use if it was not followed by a proper response
                conversation_turns.pop()
                last_tool_use_request = False

            role = (
                ConversationRoleGemini.USER.value
                if message.actor == MessageThreadActor.USER
                else ConversationRoleGemini.MODEL.value
            )
            parts: List[google_genai_types.Part] = []

            # Sort: TextBlockData first, then tool-related
            message_datas = list(message.message_data)
            message_datas.sort(key=lambda x: 0 if isinstance(x, TextBlockData) else 1)

            for message_data in message_datas:
                content_data = message_data.content

                if isinstance(content_data, TextBlockContent):
                    parts.append(google_genai_types.Part.from_text(text=content_data.text))
                    last_tool_use_request = False

                elif isinstance(content_data, ToolUseResponseContent):
                    if last_tool_use_request and conversation_turns and conversation_turns[-1].parts[-1].function_call:
                        tool_response = google_genai_types.Part.from_function_response(
                            name=content_data.tool_name, response=content_data.response
                        )
                        parts.append(tool_response)
                        last_tool_use_request = False

                elif isinstance(content_data, ToolUseRequestContent):
                    function_call = google_genai_types.Part.from_function_call(
                        name=content_data.tool_name, args=content_data.tool_input
                    )
                    parts.append(function_call)
                    last_tool_use_request = True

                elif isinstance(content_data, ExtendedThinkingContent):
                    continue

                else:
                    attachment_id = content_data.attachment_id
                    attachment_data = await attachment_data_task_map[attachment_id]
                    if attachment_data.attachment_metadata.file_type.startswith("image/"):
                        parts.append(
                            google_genai_types.Part.from_bytes(
                                data=attachment_data.object_bytes,
                                mime_type=attachment_data.attachment_metadata.file_type,
                            )
                        )
                    last_tool_use_request = False

            if parts:
                conversation_turns.append(google_genai_types.Content(role=role, parts=parts))

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
        cache_config: PromptCacheConfig = PromptCacheConfig(  # Gemini caching is generally automatic
            tools=True, system_message=True, conversation=True
        ),
    ) -> Dict[str, Any]:
        """
        Formats the conversation for Vertex AI's Gemini model.

        Args:
            llm_model: The specific model requested (e.g., LLModels.GEMINI_2_5_PRO).
            prompt: Contains the initial system and user messages.
            tool_use_response: The result from a previous tool execution.
            previous_responses: History of the conversation.
            tools: Available tools for the model.
            tool_choice: How to handle tool selection (none, auto, required).
            cache_config: Caching configuration (mostly informational for Gemini).
            search_web: Add a tool to search web

        Returns:
            Dict[str, Any]: Payload containing 'contents', 'tools', 'system_instruction', 'tool_config'.
        """

        # search_web = kwargs.get("search_web", False)
        search_web = False  # Gemini does not support web search tool, so we set it to False
        if tools and search_web:
            raise BadRequestException("Functional tools and Web search tool can not be used together")
        model_config = self._get_model_config(llm_model)
        system_instruction: Optional[google_genai_types.Part] = None
        tool_config: Optional[google_genai_types.ToolConfig] = None

        # 1. Handle System Prompt
        if prompt and prompt.system_message:
            system_instruction = google_genai_types.Part.from_text(text=prompt.system_message)

        # 2. Process Conversation History (previous_responses)
        contents: List[google_genai_types.Content] = await self.get_conversation_turns(
            previous_responses, attachment_data_task_map
        )

        # 3. Handle Current User Prompt
        user_parts: List[google_genai_types.Part] = []

        if prompt and prompt.user_message:
            user_parts.append(google_genai_types.Part.from_text(text=prompt.user_message))

        if attachments:
            for attachment in attachments:
                attachment_data = await attachment_data_task_map[attachment.attachment_id]
                if attachment_data:
                    user_parts.append(
                        google_genai_types.Part.from_bytes(
                            data=attachment_data.object_bytes, mime_type=attachment_data.attachment_metadata.file_type
                        )
                    )

        if user_parts:
            contents.append(google_genai_types.Content(role=ConversationRoleGemini.USER.value, parts=user_parts))

        # 4. Handle Tool Use Response (if provided for this specific call)
        if tool_use_response:
            tool_response = google_genai_types.Part.from_function_response(
                name=tool_use_response.content.tool_name,
                response=tool_use_response.content.response,
            )
            contents.append(google_genai_types.Content(parts=[tool_response], role=ConversationRoleGemini.USER.value))

        # 5. Handle Tools Definition
        tools = sorted(tools, key=lambda x: x.name) if tools else []
        formatted_tools = []
        for tool in tools:
            formatted_tool = google_genai_types.Tool(
                function_declarations=[
                    google_genai_types.FunctionDeclaration(
                        description=tool.description,
                        name=tool.name,
                        parameters=google_genai_types.Schema(**tool.input_schema.model_dump(mode="json")),
                    )
                ]
            )
            formatted_tools.append(formatted_tool)
        if search_web:
            formatted_tools = [google_genai_types.Tool(google_search=google_genai_types.GoogleSearch())]
        # Basic safety settings (optional, configure as needed)
        safety_settings = {}
        return {
            "max_tokens": model_config["MAX_TOKENS"],
            "contents": contents,
            "tools": formatted_tools,
            "tool_config": tool_config,
            "system_instruction": system_instruction,
            "safety_settings": safety_settings,
        }

    def _parse_non_streaming_response(
        self, response: google_genai_types.GenerateContentResponse
    ) -> NonStreamingResponse:
        """
        Parses the non-streaming response from Vertex AI's Gemini model.

        Args:
            response: The raw GenerateContentResponse from the Vertex AI API.

        Returns:
            NonStreamingResponse: Parsed response in your application's format.
        """
        content_blocks: List[ResponseData] = []
        input_tokens = 0
        output_tokens = 0

        # Extract usage data
        if response.usage_metadata:
            input_tokens = response.usage_metadata.prompt_token_count
            output_tokens = response.usage_metadata.candidates_token_count  # Sum across candidates if multiple

        # Check for safety blocks or empty candidates
        if not response.candidates:
            # Handle cases where the response was blocked or no content generated
            # You might want to check response.prompt_feedback for block reasons
            print(f"Warning: No candidates found in response. Feedback: {response.prompt_feedback}")
            # Return an empty or error response structure
            return NonStreamingResponse(content=[], usage=LLMUsage(input=input_tokens, output=output_tokens))

        # Process the first candidate (usually the only one unless configured otherwise)
        candidate = response.candidates[0]

        # Check finish reason (e.g., STOP, MAX_TOKENS, SAFETY, RECITATION, TOOL_CALL)
        _finish_reason = candidate.finish_reason.name
        # You might log or handle different finish reasons specifically
        # print(f"Model finish reason: {finish_reason}")

        # Check for safety ratings
        if candidate.safety_ratings:
            for rating in candidate.safety_ratings:
                if rating.blocked:
                    print(f"Warning: Response content blocked due to safety rating: {rating.category.name}")
                    # Decide how to handle blocked content (e.g., return empty, raise error)

        # Extract content parts (text, function calls)
        if candidate.content and candidate.content.parts:
            for part in candidate.content.parts:
                if part.text:
                    content_blocks.append(TextBlockData(content=TextBlockContent(text=part.text)))
                elif part.function_call:
                    content_blocks.append(
                        ToolUseRequestData(
                            type=ContentBlockCategory.TOOL_USE_REQUEST,
                            content=ToolUseRequestContent(
                                tool_input=part.function_call.args,
                                tool_name=part.function_call.name,
                                tool_use_id=str(uuid.uuid4()),
                            ),
                        )
                    )

        return NonStreamingResponse(
            content=content_blocks,
            usage=LLMUsage(input=input_tokens or 0, output=output_tokens or 0),
        )

    async def _parse_streaming_response(
        self, response: AsyncIterator[google_genai_types.GenerateContentResponse]
    ) -> StreamingResponse:
        usage = LLMUsage(input=0, output=0, cache_read=0, cache_write=0)
        streaming_completed = False
        accumulated_events = []

        async def stream_content() -> AsyncIterator[StreamingEvent]:
            nonlocal usage
            nonlocal streaming_completed
            nonlocal accumulated_events
            current_running_block_type: Optional[ContentBlockCategory] = None
            async for chunk in response:
                try:
                    event_blocks, event_block_category, event_usage = await self._get_parsed_stream_event(
                        chunk, current_running_block_type
                    )
                    if event_usage:
                        usage += event_usage
                    if event_blocks:
                        current_running_block_type = event_block_category
                        for event_block in event_blocks:
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

    async def _get_parsed_stream_event(
        self,
        chunk: google_genai_types.GenerateContentResponse,
        current_running_block_type: Optional[ContentBlockCategory] = None,
    ) -> Tuple[List[Optional[StreamingEvent]], Optional[ContentBlockCategory], Optional[LLMUsage]]:
        event_blocks: List[StreamingEvent] = []
        usage = LLMUsage(input=0, output=0, cache_read=0, cache_write=0)
        candidate = chunk.candidates[0]
        part: google_genai_types.Part = candidate.content.parts[0]
        # Block type is changing, so mark current running block end and start new block.
        if current_running_block_type != ContentBlockCategory.TEXT_BLOCK and part.text:
            if current_running_block_type == ContentBlockCategory.TOOL_USE_REQUEST:
                event_block = ToolUseRequestEnd()
                event_blocks.append(event_block)
            event_block = TextBlockStart()
            event_blocks.append(event_block)
            current_running_block_type = ContentBlockCategory.TEXT_BLOCK
        elif current_running_block_type != ContentBlockCategory.TOOL_USE_REQUEST and part.function_call:
            if current_running_block_type == ContentBlockCategory.TEXT_BLOCK:
                event_block = TextBlockEnd()
                event_blocks.append(event_block)
            function_call: google_genai_types.FunctionCall = part.function_call
            event_block = ToolUseRequestStart(
                content=ToolUseRequestStartContent(
                    tool_name=function_call.name, tool_use_id=function_call.id or str(uuid.uuid4())
                )
            )
            event_blocks.append(event_block)
            current_running_block_type = ContentBlockCategory.TOOL_USE_REQUEST
        # ============================================================================== #

        # ============================ Add data of current block ======================= #
        if part.text:
            event_block = TextBlockDelta(content=TextBlockDeltaContent(text=part.text))
            event_blocks.append(event_block)
        elif part.function_call:
            event_block = ToolUseRequestDelta(
                content=ToolUseRequestDeltaContent(input_params_json_delta=json.dumps(part.function_call.args))
            )
            event_blocks.append(event_block)
        if candidate.finish_reason:
            if chunk.usage_metadata.prompt_token_count or chunk.usage_metadata.candidates_token_count:
                usage.input = chunk.usage_metadata.prompt_token_count
                usage.output = chunk.usage_metadata.candidates_token_count
            event_block = None
            if current_running_block_type == ContentBlockCategory.TEXT_BLOCK:
                event_block = TextBlockEnd()
            elif current_running_block_type == ContentBlockCategory.TOOL_USE_REQUEST:
                event_block = ToolUseRequestEnd()
            event_blocks.append(event_block)

        return event_blocks, current_running_block_type, usage

    async def call_service_client(
        self,
        llm_payload: Dict[str, Any],
        model: LLModels,
        stream: bool = False,
        response_type: Optional[str] = None,
        response_schema=None,
    ) -> UnparsedLLMCallResponse:
        """
        Calls the Vertex AI service client.

        Args:
            llm_payload: The structured payload from build_llm_payload.
            model: The LLModels enum value specifying which model to use.
            stream: Whether to use streaming mode.
            response_type: Optional response format hint (less common for Gemini chat).
            response_schema: Optional: response structure

        Returns:
            Either a NonStreamingResponse or an AsyncIterator for streaming.
        """
        model_config = self._get_model_config(model)  # Get your internal config
        vertex_model_name = model_config.get("NAME")
        max_output_tokens = model_config.get("MAX_TOKENS") or 8192
        client = GeminiServiceClient()

        if stream:
            response = await client.get_llm_stream_response(
                model_name=vertex_model_name,
                contents=llm_payload["contents"],
                tools=llm_payload.get("tools"),
                tool_config=llm_payload.get("tool_config"),
                system_instruction=llm_payload.get("system_instruction"),
                max_output_tokens=max_output_tokens,
            )
            return await self._parse_streaming_response(response)
        else:
            response = await client.get_llm_non_stream_response(
                model_name=vertex_model_name,
                contents=llm_payload["contents"],
                tools=llm_payload.get("tools"),
                tool_config=llm_payload.get("tool_config"),
                system_instruction=llm_payload.get("system_instruction"),
                max_output_tokens=max_output_tokens,
            )
            return self._parse_non_streaming_response(response)
