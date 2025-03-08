from typing import Any, Dict

from app.backend_common.services.llm.dataclasses.main import UserAndSystemMessages
from app.backend_common.services.llm.prompts.llm_base_prompts.gpt_4o import (
    BaseGPT4OPrompt,
)

from ...dataclasses.main import PromptFeatures


class GPT4OPRSummarizationPrompt(BaseGPT4OPrompt):
    prompt_type = PromptFeatures.PR_SUMMARIZATION.value

    def __init__(self, params: Dict[str, Any]):
        self.params = params

    def get_prompt(self) -> UserAndSystemMessages:
        system_message = """
            Your name is SCRIT, receiving a user's comment thread carefully examine the smart code review analysis. 
            If the comment involves inquiries about code improvements or other technical discussions, evaluate the 
            provided pull request (PR) diff and offer appropriate resolutions. Otherwise, respond directly to 
            the posed question without delving into the PR diff. 
            include all the corrective_code inside ``` CODE ``` markdown"
        """

        user_message = f"""
            What does the following PR do ?
            Pull Request Title
            {self.params['PULL_REQUEST_TITLE']}

            Pull Request Diff:
            {self.params['PR_DIFF_WITHOUT_LINE_NUMBER']}
        """

        return UserAndSystemMessages(user_message=user_message, system_message=system_message)
