# flake8: noqa
from torpedo import CONFIG

from app.main.blueprints.deputy_dev.constants.constants import AgentTypes, TokenTypes
from app.main.blueprints.deputy_dev.services.code_review.agent_services.agent_base import (
    AgentServiceBase,
)
from app.main.blueprints.deputy_dev.services.code_review.context.context_service import (
    ContextService,
)


class OpenAIPRSummaryAgent(AgentServiceBase):
    def __init__(self, context_service: ContextService, is_reflection_enabled: bool):
        super().__init__(context_service, is_reflection_enabled, AgentTypes.PR_SUMMARY.value)

    def get_with_reflection_system_prompt_pass1(self):
        return """
        Your name is DeputyDev, receiving a user's comment thread carefully examine the smart code review analysis. 
        Your task is to summarise what the PR is doing.
        include all the code changes inside ``` CODE ``` markdown".
        """

    def get_with_reflection_user_prompt_pass1(self):
        return """
        Here is the information for the pull request you need to review:
        Pull Request Title:
        <pull_request_title>
        {$PULL_REQUEST_TITLE}
        </pull_request_title>

        Pull Request Description:
        <pull_request_description>
        {$PULL_REQUEST_DESCRIPTION}
        </pull_request_description>

        Pull Request Diff:
        <pull_request_diff>
        {$PR_DIFF_WITHOUT_LINE_NUMBER}
        </pull_request_diff>
        """

    def get_with_reflection_system_prompt_pass2(self):
        pass

    def get_with_reflection_user_prompt_pass2(self):
        pass

    def get_additional_info_prompt(self, tokens_info, reflection_iteration):
        additional_info = super().get_additional_info_prompt(tokens_info, reflection_iteration)
        additional_info.update(
            {
                "model": CONFIG.config["FEATURE_MODELS"]["PR_SUMMARY"],
            }
        )
        return additional_info

    async def get_without_reflection_prompt(self):
        return {
            "system_message": self.get_without_reflection_system_prompt(),
            "user_message": await self.format_user_prompt(self.get_without_reflection_user_prompt()),
            "structure_type": "text",
            "parse": False,
        }

    def get_agent_specific_tokens_data(self):
        return {
            TokenTypes.PR_TITLE.value: self.context_service.pr_title_tokens,
            TokenTypes.PR_DESCRIPTION.value: self.context_service.pr_description_tokens,
            TokenTypes.PR_DIFF_TOKENS.value: self.context_service.pr_diff_tokens,
        }
