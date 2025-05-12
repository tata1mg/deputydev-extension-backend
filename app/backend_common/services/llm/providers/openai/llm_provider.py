from typing import Any, Dict, List, Optional

from openai.types.chat import ChatCompletion

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
        feedback: str = None,
        cache_config: PromptCacheConfig = PromptCacheConfig(
            tools=True, system_message=True, conversation=True
        ),  # by default, OpenAI uses caching, we cannot configure it
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
            raise ValueError("Tools are not supported for OpenAI")

        if previous_responses:
            raise ValueError("Previous responses are not supported for OpenAI")

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
            usage=LLMUsage(
                input=response.usage.prompt_tokens,
                output=response.usage.completion_tokens,
            )
            if response.usage
            else LLMUsage(input=0, output=0),
        )

    async def call_service_client(
        self, llm_payload: Dict[str, Any], model: LLModels, stream: bool = False, response_type: Optional[str] = None
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

        if stream:
            raise ValueError("Stream is not supported for OpenAI")

        model_config = self._get_model_config(model)

        response = await OpenAIServiceClient().get_llm_non_stream_response(
            conversation_messages=llm_payload["conversation_messages"],
            model=model_config["NAME"],
            response_type=response_type,
        )
        return self._parse_non_streaming_response(response)
