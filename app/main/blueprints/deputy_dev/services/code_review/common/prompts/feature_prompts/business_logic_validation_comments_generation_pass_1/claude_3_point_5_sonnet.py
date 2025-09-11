from typing import Any, Dict

from deputydev_core.llm_handler.dataclasses.main import UserAndSystemMessages

from app.backend_common.dataclasses.dataclasses import PromptCategories
from app.main.blueprints.deputy_dev.constants.constants import (
    CUSTOM_PROMPT_INSTRUCTIONS,
    AgentFocusArea,
)

from ...base_prompts.claude_3_point_5_sonnet_comment_creation import (
    BaseClaude3Point5SonnetCommentCreationPrompt,
)
from ...dataclasses.main import PromptFeatures


class Claude3Point5BusinessLogicValidationCommentsGenerationPass1Prompt(BaseClaude3Point5SonnetCommentCreationPrompt):
    prompt_type = PromptFeatures.BUSINESS_LOGIC_VALIDATION_COMMENTS_GENERATION_PASS_1.value
    prompt_category = PromptCategories.CODE_REVIEW.value

    def __init__(self, params: Dict[str, Any]) -> None:
        self.params = params
        self.agent_focus_area = AgentFocusArea.BUSINESS_LOGIC_VALIDATION.value

    def get_system_prompt(self) -> str:
        return self.get_tools_specific_system_message(self.params)

    def get_prompt(self) -> UserAndSystemMessages:
        system_message = self.get_system_prompt()

        cached_message = self.get_user_cached_message_template(self.params)

        user_message = f"""
            You are a senior developer tasked with reviewing a pull request for functional correctness. Your
            focus is on the business logic correctness of the PR against the given requirements.
            
            Understand the requirements:
            <user_story>
            {self.params["USER_STORY"]}
            </user_story>
            
            <product_research_document>
            {self.params["PRODUCT_RESEARCH_DOCUMENT"]}
            </product_research_document>
            
            Instructions to Review: 
            
            1. Analyze the changes:
            - Compare the changes in the pull request diff against the requirements in the user story and
            product research document.
            - Identify any discrepancies or misalignment's between the implemented changes and the stated
            requirements.
            - Focus solely on business logic correctness. Do not comment on other aspects such as security, code communication, performance, code maintainability, errors etc or provide
            appreciation for correct implementations..
            
            2. Prepare your review comments:
            - Only create a comment for unique, significant issues that directly impact business requirements.
            - Do not repeat similar comments for multiple instances of the same issue.
            - Do not provide general observations or suggestions unless they are critical to meeting the
            business requirements.

            Remember:
            - Map exactly 1 comment to each comment tag in the output response.
            - If you find something like certain change can have cascading effect in some other files too, Provide the exact file path, line number and the code snippet affected by the change.
            - Focus only on business logic correctness. Do not comment on any other aspects of code review.
            - Do not change the provided bucket name.
            - Provide clear and actionable feedback in your comments only for critical issues.
            - Use the confidence score to indicate how certain you are about each issue you raise.
            - Need not to do the appreciation comments for the things that are done correctly.
            - <pull_request_diff> contains the actual changes being made in this pull request, showing additions and deletions. 
                This is the primary focus for review comments. The diff shows:
                - Added lines (prefixed with +)
                - Removed lines (prefixed with -)
                - Context lines (no prefix)
                Only added lines and Removed lines changes should receive direct review comments.
            -  Comment ONLY on code present in <pull_request_diff> and Use <contextually_related_code_snippets> 
            only for understanding impact of change. 
            -   Do not comment on unchanged code unless directly impacted by the changes.
            -   Do not duplicate comments for similar issues across different locations.
            -   If you are suggesting any comment that is already catered please don't include those comment in response.
            -  Use all the required tools if you need to fetch some piece of code based on it. 
            - Provide the exact, correct bucket name relevant to the issue. Ensure that the value is never left as a placeholder like "$BUCKET".
            
            Your review should help ensure that the changes in the pull request accurately implement the
            requirements specified in the user story and product research document.
        """

        if self.params.get("CUSTOM_PROMPT"):
            user_message = f"{user_message}\n{CUSTOM_PROMPT_INSTRUCTIONS}\n{self.params['CUSTOM_PROMPT']}"

        return UserAndSystemMessages(
            user_message=user_message, system_message=system_message, cached_message=cached_message
        )

    def get_finalize_iteration_breached_prompt(self) -> UserAndSystemMessages:
        user_message = self.get_force_finalize_user_message()
        system_message = self.get_system_prompt()
        return UserAndSystemMessages(user_message=user_message, system_message=system_message)
