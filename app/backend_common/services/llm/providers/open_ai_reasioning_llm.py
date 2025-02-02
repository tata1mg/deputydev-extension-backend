from typing import Dict, List

from app.backend_common.services.llm.providers.openai_llm import OpenaiLLM


class OpenAIReasoningLLM(OpenaiLLM):
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
            {"role": "user", "content": prompt["user_message"] + prompt["system_message"]},
        ]
        return message
