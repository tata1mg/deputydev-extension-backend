from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from app.backend_common.utils.sanic_wrapper import CONFIG
from app.main.blueprints.deputy_dev.constants.constants import TokenTypes
from app.main.blueprints.deputy_dev.services.code_review.common.agents.dataclasses.main import (
    AgentRunResult,
    AgentTypes,
)
from app.main.blueprints.deputy_dev.services.code_review.common.prompts.dataclasses.main import (
    PromptFeatures,
)
from app.main.blueprints.deputy_dev.services.code_review.ide_review.context.ide_review_context_service import (
    IdeReviewContextService,
)
from deputydev_core.llm_handler.core.handler import LLMHandler
from deputydev_core.llm_handler.dataclasses.main import (
    NonStreamingParsedLLMCallResponse,
    UserAndSystemMessages,
)
from deputydev_core.llm_handler.models.dto.message_thread_dto import LLModels
from deputydev_core.services.tiktoken import TikToken
from deputydev_core.utils.app_logger import AppLogger


class BaseCodeReviewAgent(ABC):
    agent_type: AgentTypes
    agent_name: str
    is_dual_pass: bool
    prompt_features: List[PromptFeatures]

    def __init__(
        self,
        context_service: IdeReviewContextService,
        llm_handler: LLMHandler[PromptFeatures],
        model: LLModels,
    ) -> None:
        self.context_service = context_service
        self.tiktoken = TikToken()
        self.agent_name = self.agent_type.value
        self.llm_handler = llm_handler
        self.model = model

    async def should_execute(self) -> bool:
        """
        Check if the agent should be executed based on the agent settings.
        This method should be overridden by the child class if the agent has specific conditions
        By default, it returns True
        """
        return True

    def get_agent_specific_tokens_data(self) -> Dict[str, Any]:
        """
        This method should be overridden by the child class to return the agent specific tokens data
        """
        return {}

    def get_tokens_data(self, rendered_messages: UserAndSystemMessages) -> Dict[str, int]:
        tokens_info = self.get_agent_specific_tokens_data()
        tokens_info[TokenTypes.SYSTEM_PROMPT.value] = self.tiktoken.count(rendered_messages.system_message or "")
        tokens_info[TokenTypes.USER_PROMPT.value] = self.tiktoken.count(rendered_messages.user_message)
        return tokens_info

    def has_exceeded_token_limit(self, rendered_messages: UserAndSystemMessages) -> bool:
        token_count = self.tiktoken.count(rendered_messages.system_message or "" + rendered_messages.user_message)
        model_input_token_limit = CONFIG.config["LLM_MODELS"][self.model.value]["INPUT_TOKENS_LIMIT"]
        if token_count <= model_input_token_limit:
            return False
        AppLogger.log_info(
            f"Prompt: {self.agent_name} token count {token_count} exceeds the allowed limit of {model_input_token_limit}."
        )
        return True

    @abstractmethod
    async def required_prompt_variables(self) -> Dict[str, Optional[str]]:
        """
        Return the required prompt variables for the agent
        """
        raise NotImplementedError("required_prompt_variables method should be implemented by the child class")

    async def run_agent(self, session_id: int) -> AgentRunResult:
        """
        Run the agent and return the agent run result
        """
        total_passes = 1 if not self.is_dual_pass else 2
        tokens_data: Dict[str, Dict[str, Any]] = {}
        for pass_num in range(1, total_passes + 1):
            prompt_feature = self.prompt_features[pass_num - 1]  # 0 indexed

            # check if the token limit has been exceeded
            prompt_vars = await self.required_prompt_variables()
            prompt_handler = self.llm_handler.prompt_handler_map.get_prompt(
                model_name=self.model, feature=prompt_feature
            )(prompt_vars)
            user_and_system_messages = prompt_handler.get_prompt()
            current_tokens_data = self.get_tokens_data(user_and_system_messages)
            token_limit_exceeded = self.has_exceeded_token_limit(user_and_system_messages)

            token_key = f"{self.agent_name}PASS_{pass_num}"
            tokens_data[token_key] = current_tokens_data

            if token_limit_exceeded:
                return AgentRunResult(
                    agent_result=None,
                    prompt_tokens_exceeded=True,
                    agent_name=self.agent_name,
                    agent_type=self.agent_type,
                    model=self.model,
                    tokens_data=tokens_data,
                )

            llm_response = await self.llm_handler.start_llm_query(
                session_id=session_id,
                prompt_feature=prompt_feature,
                llm_model=self.model,
                prompt_vars=prompt_vars,
            )

            if not isinstance(llm_response, NonStreamingParsedLLMCallResponse):
                raise ValueError(f"LLM Response is not of type NonStreamingParsedLLMCallResponse: {llm_response}")

            tokens_data[token_key].update(
                {
                    "input_tokens": llm_response.usage.input,
                    "output_tokens": llm_response.usage.output,
                }
            )

            # these agents only support one response block in entire list
            # if this is not the case, we can override this method in the child class
            rendered_messages = llm_response.parsed_content[0]
            last_pass_result = rendered_messages
        return AgentRunResult(
            agent_result=last_pass_result,
            prompt_tokens_exceeded=False,
            agent_name=self.agent_name,
            agent_type=self.agent_type,
            model=self.model,
            tokens_data=tokens_data,
            display_name=self.get_display_name(),
        )

    def get_display_name(self) -> str:
        pass
