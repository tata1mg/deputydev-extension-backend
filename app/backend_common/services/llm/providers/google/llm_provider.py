from typing import (  # Added AsyncIterator
    Any,
    AsyncIterator,
    Dict,
    List,
    Optional,
    Union,
)

from vertexai.generative_models import (  # Add Vertex AI imports
    Content,
    GenerationResponse,
    HarmCategory,
    Part,
    SafetySetting,
    Tool,
    ToolConfig,
)

# Your existing DTOs and base class
from app.backend_common.constants.constants import LLMProviders
from app.backend_common.models.dto.message_thread_dto import (
    LLModels,
    LLMUsage,
    MessageThreadDTO,
    ResponseData,
    TextBlockContent,
    TextBlockData,
    ToolUseResponseData,
)
from app.backend_common.service_clients.gemini.gemini import GeminiServiceClient
from app.backend_common.services.llm.base_llm_provider import BaseLLMProvider
from app.backend_common.services.llm.dataclasses.main import (
    ConversationTool,
    NonStreamingResponse,
    PromptCacheConfig,
    UserAndSystemMessages,
)


class Google(BaseLLMProvider):
    def __init__(self):
        super().__init__(LLMProviders.GOOGLE.value)

    def build_llm_payload(
        self,
        llm_model: LLModels,
        prompt: Optional[UserAndSystemMessages] = None,
        tool_use_response: Optional[ToolUseResponseData] = None,
        previous_responses: List[MessageThreadDTO] = [],
        tools: Optional[List[ConversationTool]] = None,
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
            cache_config: Caching configuration (mostly informational for Gemini).

        Returns:
            Dict[str, Any]: Payload containing 'contents', 'tools', 'system_instruction', 'tool_config'.
        """
        contents: List[Content] = []
        system_instruction: Optional[Part] = None
        vertex_tools: Optional[List[Tool]] = None
        tool_config: Optional[ToolConfig] = None  # Add tool_config if needed

        # 1. Handle System Prompt
        if prompt and prompt.system_message:
            system_instruction = Part.from_text(prompt.system_message)

        # 2. Process Conversation History (previous_responses)
        if previous_responses:
            raise ValueError("Chat is not supported yet in Gemini")

        # 3. Handle Current User Prompt
        if prompt and prompt.user_message:
            contents.append(Content(role="user", parts=[Part.from_text(prompt.user_message)]))

        # 4. Handle Tool Use Response (if provided for this specific call)
        if tool_use_response:
            raise ValueError("Tool use is not supported yet")

        # 5. Handle Tools Definition
        if tools:
            raise ValueError("Tool use is not supported yet")

        # Basic safety settings (optional, configure as needed)
        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: SafetySetting.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: SafetySetting.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: SafetySetting.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: SafetySetting.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        }

        return {
            "contents": contents,
            "tools": vertex_tools,
            "tool_config": tool_config,
            "system_instruction": system_instruction,
            "safety_settings": safety_settings,  # Optional
        }

    def _parse_non_streaming_response(self, response: GenerationResponse) -> NonStreamingResponse:
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
        finish_reason = candidate.finish_reason.name
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
                    # The model is requesting a tool call
                    raise ValueError("Tool use is not yet implemented for GeminiVertexAI provider.")

        return NonStreamingResponse(
            content=content_blocks,
            usage=LLMUsage(input=input_tokens, output=output_tokens),
        )

    async def call_service_client(
        self,
        llm_payload: Dict[str, Any],
        model: LLModels,
        stream: bool = False,
        response_type: Optional[str] = None,
        response_schema=None,
    ) -> Union[NonStreamingResponse, AsyncIterator[Any]]:  # Adjust return type for streaming
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
        client = GeminiServiceClient()

        if stream:
            raise ValueError("Streaming is not yet implemented for GeminiVertexAI provider.")
        else:
            response = await client.get_llm_non_stream_response(
                model_name=vertex_model_name,
                contents=llm_payload["contents"],
                tools=llm_payload.get("tools"),
                tool_config=llm_payload.get("tool_config"),
                system_instruction=llm_payload.get("system_instruction"),
            )
            return self._parse_non_streaming_response(response)
