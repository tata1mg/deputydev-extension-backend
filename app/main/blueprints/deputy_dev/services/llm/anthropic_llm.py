import json
from typing import Any, Dict, List

from torpedo import CONFIG

from app.common.service_clients.bedrock.bedrock import BedrockServiceClient
from app.main.blueprints.deputy_dev.constants.constants import LLMProviders
from app.main.blueprints.deputy_dev.services.llm.llm_interface import LLMInterface


class Anthropic(LLMInterface):
    def __init__(self):
        super().__init__(LLMProviders.ANTHROPIC.value)
        self.anthropic_client = None
        self.model_settings: dict = CONFIG.config["LLM_MODELS"]["CLAUDE_3_POINT_5_SONNET"]

    def build_llm_message(self, prompt: Dict[str, str], previous_responses: List[Any] = []):
        user_message = {"role": "user", "content": prompt["user_message"]}
        messages = (previous_responses or []) + [user_message]
        body = json.dumps(
            {
                "anthropic_version": self.model_settings["VERSION"],
                "max_tokens": self.model_settings["MAX_TOKENS"],
                "system": prompt["system_message"],
                "messages": messages,
            }
        )
        return body

    async def call_service_client(self, messages: List[Dict[str, str]], model, response_type):
        """
        Calls the OpenAI service client.

        Args:
            messages (List[Dict[str, str]]): Formatted conversation messages.

        Returns:
            str: The response from the GPT model.
        """
        anthropic_client = await self.get_service_client()
        response = await anthropic_client.get_llm_response(messages, model)
        return response

    async def get_service_client(self):
        if not self.anthropic_client:
            self.anthropic_client = BedrockServiceClient()
        return self.anthropic_client

    async def parse_response(self, response: Dict) -> tuple:
        """
        Parses the response from OpenAI's GPT model.

        Args:
            response (Dict): The raw response from the GPT model.

        Returns:
            str: Parsed text response and outpur tokens.
        """
        body = await response["body"].read()
        llm_response = json.loads(body.decode("utf-8"))
        return (
            llm_response["content"][0]["text"],
            llm_response["usage"]["input_tokens"],
            llm_response["usage"]["output_tokens"],
        )
