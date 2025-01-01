import time
from abc import ABC, abstractmethod
from string import Template

from torpedo import CONFIG

from app.common.services.tiktoken import TikToken
from app.main.blueprints.deputy_dev.constants.constants import (
    CUSTOM_PROMPT_INSTRUCTIONS,
    MultiAgentReflectionIteration,
    TokenTypes,
)
from app.main.blueprints.deputy_dev.loggers import AppLogger
from app.main.blueprints.deputy_dev.services.code_review.context.context_service import (
    ContextService,
)
from app.main.blueprints.deputy_dev.services.workspace.context_vars import (
    get_context_value,
)
from app.main.blueprints.deputy_dev.utils import repo_meta_info_prompt


class AgentServiceBase(ABC):
    def __init__(self, context_service: ContextService, is_reflection_enabled: bool, agent_name):
        self.context_service = context_service
        self.is_reflection_enabled = is_reflection_enabled
        self.agent_name = agent_name
        self.tiktoken = TikToken()
        self.model = CONFIG.config["FEATURE_MODELS"]["PR_REVIEW"]
        agent_settings = get_context_value("setting")["code_review_agent"]["agents"]
        self.comment_confidence_score = agent_settings.get(self.agent_name, {}).get("confidence_score")
        self.custom_prompt = agent_settings.get(self.agent_name, {}).get("custom_prompt", "")

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
            t1 = time.time() * 1000
            prompt = await self.get_with_reflection_prompt_pass_1()
            t2 = time.time() * 1000
            AppLogger.log_info(f"Time taken in building prompt for pass 1 - {t2 - t1} ms")
            return prompt
        elif reflection_iteration == MultiAgentReflectionIteration.PASS_2.value:
            t1 = time.time() * 1000
            prompt = await self.get_with_reflection_prompt_pass_2(previous_review_comments)
            t2 = time.time() * 1000
            AppLogger.log_info(f"Time taken in building prompt for pass 2 - {t2 - t1} ms")
            return prompt

    async def get_with_reflection_prompt_pass_1(self):
        system_message = self.get_with_reflection_system_prompt_pass1()
        system_message = self.inject_system_prompt(system_message)
        user_prompt = self.get_with_reflection_user_prompt_pass1()
        user_prompt = self.inject_custom_prompt(user_prompt)
        user_message = await self.format_user_prompt(user_prompt)
        return {
            "system_message": system_message,
            "user_message": user_message,
            "structure_type": "text",
            "parse": False,
            "exceeds_tokens": self.has_exceeded_token_limit(system_message, user_message),
        }

    async def get_with_reflection_prompt_pass_2(self, previous_review_comments):
        system_message = self.get_with_reflection_system_prompt_pass2()
        system_message = self.inject_system_prompt(system_message)
        user_prompt = self.get_with_reflection_user_prompt_pass2()
        user_prompt = self.inject_custom_prompt(user_prompt)
        user_message = await self.format_user_prompt(user_prompt, previous_review_comments)
        return {
            "system_message": system_message,
            "user_message": user_message,
            "structure_type": "xml",
            "parse": True,
            "exceeds_tokens": self.has_exceeded_token_limit(system_message, user_message),
        }

    def inject_custom_prompt(self, user_prompt):
        if self.custom_prompt and self.custom_prompt.strip():
            return f"{user_prompt}\n{CUSTOM_PROMPT_INSTRUCTIONS}\n{self.custom_prompt}"
        return user_prompt

    def inject_system_prompt(self, system_prompt):
        """
        Generates a system prompt describing the language and framework being used,
        based on the application settings.
        """
        app_settings = get_context_value("setting").get("app", {})
        repo_info_prompt = repo_meta_info_prompt(app_settings)
        return f"{system_prompt}\n{repo_info_prompt}"

    async def get_without_reflection_prompt(self):
        system_message = self.get_without_reflection_system_prompt()
        system_message = self.inject_system_prompt(system_message)
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
        user_prompt = self.get_with_reflection_user_prompt_pass1()
        user_prompt = self.inject_custom_prompt(user_prompt)
        return user_prompt

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
