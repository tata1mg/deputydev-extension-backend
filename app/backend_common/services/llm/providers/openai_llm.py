from typing import Any, Dict, List, Tuple

from app.backend_common.service_clients.openai.openai import OpenAIServiceClient
from app.backend_common.services.llm.base_llm_provider import BaseLLMProvider
from app.common.constants.constants import LLMProviders


class OpenaiLLM(BaseLLMProvider):
    def __init__(self):
        super().__init__(LLMProviders.OPENAI.value)

    """LLM manager for handling interactions with OpenAI's GPT models."""

    async def parse_response(self, response: Dict) -> Tuple[str, int, int]:
        """
        Parses the response from OpenAI's GPT model.

        Args:
            response (Dict): The raw response from the GPT model.

        Returns:
            str: Parsed text response and outpur tokens.
        """
        return (
            response.choices[0].message.content,
            response.usage.prompt_tokens,
            response.usage.completion_tokens,
        )

    async def call_service_client(self, messages: List[Dict[str, str]], model: str, response_type: str) -> Any:
        """
        Calls the OpenAI service client.

        Args:
            messages (List[Dict[str, str]]): Formatted conversation messages.

        Returns:
            str: The response from the GPT model.
        """
        response = await OpenAIServiceClient().get_llm_response(
            conversation_messages=messages, model=model, response_type=response_type
        )
        return response

    def build_llm_message(
        self, prompt: Dict[str, str], previous_responses: List[Dict[str, str]] = []
    ) -> List[Dict[str, str]]:
        """
        Formats the conversation for OpenAI's GPT model.

        Args:
            prompt (Dict[str, str]): A prompt object.
            previous_responses (List[Dict[str, str]] ): previous messages to pass to LLM

        Returns:
            List[Dict[str, str]]: A formatted list of message dictionaries.
        """
        message = [
            {"role": "system", "content": prompt["system_message"]},
            {"role": "user", "content": prompt["user_message"]},
        ]
        return message
