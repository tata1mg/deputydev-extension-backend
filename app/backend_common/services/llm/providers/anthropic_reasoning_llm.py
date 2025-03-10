from typing import Dict, List
import json

from app.backend_common.services.llm.providers.anthropic_llm import Anthropic


class AnthropicReasoningLLM(Anthropic):
    def build_llm_message(self, prompt: Dict[str, str], previous_responses: List[Dict[str, str]] = []) -> str:

        user_message = {"role": "user", "content": prompt["user_message"]}
        messages = (previous_responses or []) + [user_message]
        body = json.dumps(
            {
                "anthropic_version": self.model_settings["VERSION"],
                "max_tokens": self.model_settings["MAX_TOKENS"],
                "system": prompt["system_message"],
                "messages": messages,
                "thinking": {
                    "type": "enabled",
                    "budget_tokens": self.model_settings["THINKING_BUDGET_TOKENS"]
                },
            }
        )
        return body
