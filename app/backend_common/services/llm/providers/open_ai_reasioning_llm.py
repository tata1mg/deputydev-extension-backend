from typing import Any, Dict, List, Optional

from app.backend_common.services.llm.dataclasses.main import (
    ConversationTools,
    ConversationTurn,
    PromptCacheConfig,
    UserAndSystemMessages,
)
from app.backend_common.services.llm.providers.openai_llm import OpenaiLLM


class OpenAIReasoningLLM(OpenaiLLM):
    def build_llm_payload(
        self,
        prompt: UserAndSystemMessages,
        previous_responses: List[ConversationTurn] = [],
        tools: Optional[ConversationTools] = None,
        cache_config: PromptCacheConfig = PromptCacheConfig(tools=False, system_message=False, conversation=False),
    ) -> Dict[str, Any]:
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
