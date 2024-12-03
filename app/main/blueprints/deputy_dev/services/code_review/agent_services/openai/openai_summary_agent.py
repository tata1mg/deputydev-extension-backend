# flake8: noqa
from torpedo import CONFIG

from app.main.blueprints.deputy_dev.constants.constants import (
    AgentTypes,
    PRStatus,
    TokenTypes,
)
from app.main.blueprints.deputy_dev.services.code_review.agent_services.agent_base import (
    AgentServiceBase,
)
from app.main.blueprints.deputy_dev.services.code_review.context.context_service import (
    ContextService,
)


class OpenAIPRSummaryAgent(AgentServiceBase):
    def __init__(self, context_service: ContextService, is_reflection_enabled: bool):
        super().__init__(context_service, is_reflection_enabled, AgentTypes.PR_SUMMARY.value)
        # TODO: for now not picking model from setting, This can be updated if required:
        # setting = get_context_value("setting")
        # self.model = setting[AgentTypes.PR_SUMMARY.value]["model"]
        self.model = CONFIG.config["FEATURE_MODELS"]["PR_SUMMARY"]

    def get_with_reflection_system_prompt_pass1(self):
        return """
        Your name is SCRIT, receiving a user's comment thread carefully examine the smart code review analysis. 
        If the comment involves inquiries about code improvements or other technical discussions, evaluate the 
        provided pull request (PR) diff and offer appropriate resolutions. Otherwise, respond directly to 
        the posed question without delving into the PR diff. 
        include all the corrective_code inside ``` CODE ``` markdown"
        """

    def get_with_reflection_user_prompt_pass1(self):
        return """
        What does the following PR do ?
        Pull Request Diff:
        {$PR_DIFF_WITHOUT_LINE_NUMBER}
        """

    def get_with_reflection_system_prompt_pass2(self):
        pass

    def get_with_reflection_user_prompt_pass2(self):
        pass

    def get_additional_info_prompt(self, tokens_info, reflection_iteration):
        additional_info = super().get_additional_info_prompt(tokens_info, reflection_iteration)
        additional_info.update(
            {
                "model": self.model,
            }
        )
        return additional_info

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

    def get_agent_specific_tokens_data(self):
        return {
            TokenTypes.PR_TITLE.value: self.context_service.pr_title_tokens,
            TokenTypes.PR_DESCRIPTION.value: self.context_service.pr_description_tokens,
            TokenTypes.PR_DIFF_TOKENS.value: self.context_service.pr_diff_tokens,
        }

    async def should_execute(self):
        pr_status = self.context_service.get_pr_status()
        if pr_status in [PRStatus.MERGED.value, PRStatus.DECLINED.value]:
            return False
        return True
