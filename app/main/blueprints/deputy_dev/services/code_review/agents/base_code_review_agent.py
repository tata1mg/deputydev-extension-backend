from abc import ABC
from typing import Dict

from deputydev_core.services.tiktoken import TikToken
from deputydev_core.utils.app_logger import AppLogger
from torpedo import CONFIG

from app.backend_common.services.llm.dataclasses.main import UserAndSystemMessages
from app.main.blueprints.deputy_dev.constants.constants import TokenTypes
from app.main.blueprints.deputy_dev.services.code_review.agents.dataclasses.main import (
    AgentTypes,
)
from app.main.blueprints.deputy_dev.services.code_review.context.context_service import (
    ContextService,
)


class BaseCodeReviewAgent(ABC):
    agent_type: AgentTypes
    agent_name: str

    def __init__(self, context_service: ContextService, is_reflection_enabled: bool):
        self.context_service = context_service
        self.is_reflection_enabled = is_reflection_enabled
        self.tiktoken = TikToken()
        self.agent_name = self.agent_type.value
        self.model = CONFIG.config["FEATURE_MODELS"]["PR_REVIEW"]

    async def should_execute(self) -> bool:
        """
        Check if the agent should be executed based on the agent settings.
        This method should be overridden by the child class if the agent has specific conditions
        By default, it returns True
        """
        return True

    def get_agent_specific_tokens_data(self) -> Dict[str, int]:
        """
        This method should be overridden by the child class to return the agent specific tokens data
        """
        return {}

    def get_tokens_data(self, rendered_messages: UserAndSystemMessages):
        tokens_info = self.get_agent_specific_tokens_data()
        tokens_info[TokenTypes.SYSTEM_PROMPT.value] = self.tiktoken.count(rendered_messages.system_message or "")
        tokens_info[TokenTypes.USER_PROMPT.value] = self.tiktoken.count(rendered_messages.user_message)
        return tokens_info

    def has_exceeded_token_limit(self, rendered_messages: UserAndSystemMessages) -> bool:
        token_count = self.tiktoken.count(rendered_messages.system_message or "" + rendered_messages.user_message)
        model_input_token_limit = CONFIG.config["LLM_MODELS"][self.model]["INPUT_TOKENS_LIMIT"]
        if token_count <= model_input_token_limit:
            return False
        AppLogger.log_info(
            f"Prompt: {self.agent_name} token count {token_count} exceeds the allowed limit of {model_input_token_limit}."
        )
        return True
