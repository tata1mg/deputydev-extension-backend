from abc import ABC, abstractmethod
from string import Template

from torpedo import CONFIG

from app.main.blueprints.deputy_dev.constants.constants import (
    MultiAgentReflectionIteration,
    TokenTypes,
)
from app.main.blueprints.deputy_dev.loggers import AppLogger
from app.main.blueprints.deputy_dev.services.code_review.context.context_service import (
    ContextService,
)
from app.main.blueprints.deputy_dev.services.tiktoken import TikToken


class AgentServiceBase(ABC):
    def __init__(self, context_service: ContextService, is_reflection_enabled: bool, agent_name):
        self.context_service = context_service
        self.is_reflection_enabled = is_reflection_enabled
        self.agent_name = agent_name
        self.comment_confidence_score = (
            CONFIG.config["AGENT_SETTINGS"].get(self.agent_name, {}).get("confidence_score_limit")
        )
        self.tiktoken = TikToken()
        self.model = CONFIG.config["FEATURE_MODELS"]["PR_REVIEW"]

    async def format_user_prompt(self, prompt: str, comments: str = None):
        prompt_variables = {
            "PULL_REQUEST_TITLE": self.context_service.get_pr_title(),
            "PULL_REQUEST_DESCRIPTION": self.context_service.get_pr_description(),
            "PULL_REQUEST_DIFF": await self.context_service.get_pr_diff(append_line_no_info=True),
            "REVIEW_COMMENTS_By_JUNIOR_DEVELOPER": comments,
            "CONTEXTUALLY_RELATED_CODE_SNIPPETS": await self.context_service.get_relevant_chunk(),
            "USER_STORY": await self.context_service.get_user_story(),
            "PRODUCT_RESEARCH_DOCUMENT": await self.context_service.get_confluence_doc(),
            "PR_DIFF_WITHOUT_LINE_NUMBER": await self.context_service.get_pr_diff(),
        }
        template = Template(prompt)
        return template.safe_substitute(prompt_variables)

    async def get_system_n_user_prompt(self, reflection_iteration=None, previous_review_comments=None):
        if self.is_reflection_enabled:
            prompt_data: dict = await self.get_with_reflection_prompt(reflection_iteration, previous_review_comments)
        else:
            prompt_data: dict = await self.get_without_reflection_prompt()

        tokens_info = self.get_tokens_data(prompt_data)
        # add common additional info
        prompt_data.update(self.get_additional_info_prompt(tokens_info, reflection_iteration))

        return prompt_data

    def get_additional_info_prompt(self, tokens_info, reflection_iteration):
        return {
            "key": self.agent_name,
            "comment_confidence_score": self.comment_confidence_score,
            "model": self.model,
            "tokens": tokens_info,
            "reflection_iteration": reflection_iteration,
        }

    async def get_with_reflection_prompt(self, reflection_iteration: str, previous_review_comments: str = None):
        if reflection_iteration == MultiAgentReflectionIteration.PASS_1.value:
            return await self.get_with_reflection_prompt_pass_1()
        elif reflection_iteration == MultiAgentReflectionIteration.PASS_2.value:
            return await self.get_with_reflection_prompt_pass_2(previous_review_comments)

    async def get_with_reflection_prompt_pass_1(self):
        system_message = self.get_with_reflection_system_prompt_pass1()
        user_message = await self.format_user_prompt(self.get_with_reflection_user_prompt_pass1())
        return {
            "system_message": system_message,
            "user_message": user_message,
            "structure_type": "text",
            "parse": False,
            "exceeds_tokens": self.has_exceeded_token_limit(system_message, user_message),
        }

    async def get_with_reflection_prompt_pass_2(self, previous_review_comments):
        system_message = self.get_with_reflection_system_prompt_pass2()
        user_message = await self.format_user_prompt(
            self.get_with_reflection_user_prompt_pass2(), previous_review_comments
        )
        return {
            "system_message": system_message,
            "user_message": user_message,
            "structure_type": "xml",
            "parse": True,
            "exceeds_tokens": self.has_exceeded_token_limit(system_message, user_message),
        }

    async def get_without_reflection_prompt(self):
        system_message = self.get_without_reflection_system_prompt()
        user_message = await self.format_user_prompt(self.get_without_reflection_user_prompt())
        return {
            "system_message": system_message,
            "user_message": user_message,
            "structure_type": "text",
            "parse": False,
            "exceeds_tokens": self.has_exceeded_token_limit(system_message, user_message),
        }

    def get_without_reflection_system_prompt(self):
        # currently as we have common prompt
        return self.get_with_reflection_system_prompt_pass1()

    def get_without_reflection_user_prompt(self):
        # currently as we have common prompt
        return self.get_with_reflection_user_prompt_pass1()

    @abstractmethod
    def get_with_reflection_system_prompt_pass1(self):
        raise NotImplementedError()

    @abstractmethod
    def get_with_reflection_system_prompt_pass2(self):
        raise NotImplementedError()

    @abstractmethod
    def get_with_reflection_user_prompt_pass1(self):
        raise NotImplementedError()

    @abstractmethod
    def get_with_reflection_user_prompt_pass2(self):
        raise NotImplementedError()

    @abstractmethod
    def get_agent_specific_tokens_data(self):
        raise NotImplementedError()

    def get_tokens_data(self, prompt_data):
        tokens_info = self.get_agent_specific_tokens_data()
        tokens_info[TokenTypes.SYSTEM_PROMPT.value] = self.tiktoken.count(prompt_data.get("system_message", ""))
        tokens_info[TokenTypes.USER_PROMPT.value] = self.tiktoken.count(prompt_data.get("user_message", ""))
        return tokens_info

    async def should_execute(self):
        return True

    def has_exceeded_token_limit(self, system_message, user_message):
        token_count = self.tiktoken.count(system_message + user_message)
        model_input_token_limit = CONFIG.config["LLM_MODELS"][self.model]["INPUT_TOKENS_LIMIT"]
        if token_count <= model_input_token_limit:
            return False
        AppLogger.log_info(
            f"Prompt: {self.agent_name} token count {token_count} exceeds the allowed limit of {model_input_token_limit}."
        )
        return True
