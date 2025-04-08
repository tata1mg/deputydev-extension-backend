from typing import Any, Dict

from app.backend_common.dataclasses.dataclasses import PromptCategories
from app.backend_common.services.llm.dataclasses.main import UserAndSystemMessages
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

    def __init__(self, params: Dict[str, Any]):
        self.params = params
        self.agent_focus_area = AgentFocusArea.BUSINESS_LOGIC_VALIDATION.value

    def get_prompt(self) -> UserAndSystemMessages:
        system_message = """
            You are a senior developer tasked with reviewing a pull request for functional correctness. Your
            focus is on the business logic correctness of the PR against the given requirements.
        """

        if self.params.get("REPO_INFO_PROMPT"):
            system_message = f"{system_message}\n{self.params['REPO_INFO_PROMPT']}"

        user_message = f"""
            Follow these
            steps to complete your review:
            
            1. Review the pull request information:
            <pull_request_title>
            {self.params['PULL_REQUEST_TITLE']}
            </pull_request_title>
            
            <pull_request_description>
            {self.params['PULL_REQUEST_DESCRIPTION']}
            </pull_request_description>
            
            <pull_request_diff>
            {self.params['PULL_REQUEST_DIFF']}
            </pull_request_diff>
            
            <contextually_related_code_snippets>
            {self.params['CONTEXTUALLY_RELATED_CODE_SNIPPETS']}
            </contextually_related_code_snippets>
            
            2. Understand the requirements:
            <user_story>
            {self.params['USER_STORY']}
            </user_story>
            
            <product_research_document>
            {self.params['PRODUCT_RESEARCH_DOCUMENT']}
            </product_research_document>
            
            3. Analyze the changes:
            - Compare the changes in the pull request diff against the requirements in the user story and
            product research document.
            - Identify any discrepancies or misalignment's between the implemented changes and the stated
            requirements.
            - Focus solely on business logic correctness. Do not comment on other aspects such as security, code communication, performance, code maintainability, errors etc or provide
            appreciation for correct implementations..
            
            4. Prepare your review comments:
            - Only create a comment for unique, significant issues that directly impact business requirements.
            - Do not repeat similar comments for multiple instances of the same issue.
            - Do not provide general observations or suggestions unless they are critical to meeting the
            business requirements.
            
            For each issue you identify, create a comment using the following format:
            
            {self.get_xml_review_comments_format(self.params['BUCKET'], self.params['AGENT_NAME'], self.agent_focus_area)} 

            Repeat the <comment> block for each issue you find regarding business logic validation.
            If you are not able to comment due to any reason, be it an error, or you think the PR is good just give the review and root comments tag and don't put anything in it.
            Example:
            <review><comments></comments></review>

            Remember:
            - Map exactly 1 comment to each comment tag in the output response.
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
            - Provide the exact, correct bucket name relevant to the issue. Ensure that the value is never left as a placeholder like "$BUCKET".
            
            Your review should help ensure that the changes in the pull request accurately implement the
            requirements specified in the user story and product research document.
        """

        if self.params.get("CUSTOM_PROMPT"):
            user_message = f"{user_message}\n{CUSTOM_PROMPT_INSTRUCTIONS}\n{self.params['CUSTOM_PROMPT']}"

        return UserAndSystemMessages(user_message=user_message, system_message=system_message)
