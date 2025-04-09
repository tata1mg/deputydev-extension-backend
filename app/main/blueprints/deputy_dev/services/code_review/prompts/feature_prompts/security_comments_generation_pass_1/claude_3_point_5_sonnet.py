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


class Claude3Point5SecurityCommentsGenerationPass1Prompt(BaseClaude3Point5SonnetCommentCreationPrompt):
    prompt_type = PromptFeatures.SECURITY_COMMENTS_GENERATION_PASS_1.value
    prompt_category = PromptCategories.CODE_REVIEW.value

    def __init__(self, params: Dict[str, Any]):
        self.params = params
        self.agent_focus_area = AgentFocusArea.SECURITY.value

    def get_prompt(self) -> UserAndSystemMessages:
        system_message = """
            You are an Expert Application Security Engineer tasked with reviewing a pull request for security
            issues and vulnerabilities. Your goal is to thoroughly analyze the provided code diff and identify
            any potential security risks.
        """
        if self.params.get("REPO_INFO_PROMPT"):
            system_message = f"{system_message}\n{self.params['REPO_INFO_PROMPT']}"

        user_message = f"""
            Follow these instructions carefully to conduct your review:

            1. Review the following information about the pull request:

            <pull_request_title>
            {self.params['PULL_REQUEST_TITLE']}
            </pull_request_title>

            <pull_request_description>
            {self.params['PULL_REQUEST_DESCRIPTION']}
            </pull_request_description>

            2. Carefully examine the code diff provided:

            <pull_request_diff>
            {self.params['PULL_REQUEST_DIFF']}
            </pull_request_diff>

            3. Conduct a comprehensive security review of the code changes, focusing on the following aspects:
            a. Input validation and sanitization
            b. Authentication and authorization
            c. Data encryption and protection
            d. Secure communication protocols
            e. Use of secure coding practices
            f. Third-party library usage and versioning
            g. Potential for injection attacks (SQL, XSS, CSRF, etc.)
            h. Secure configuration and environment variables
            i. Business logic flaws that could lead to security issues

            4. For each security issue or vulnerability you identify:
            a. Describe the issue, it's potential impact and its severity. This will be a comment on the PR.
            b. Corrected code - Rewrite the code snippet. How the code should be written ideally.
            c. File path - path of the file on which comment is being made
            d. line number - line on which comment is relevant. get this value from `<>` block at each code start in input. Return the exact value present with label `+` or `-`
            e. Confidence score - floating point confidence score of the comment between 0.0 to 1.0

            5. After completing your review, provide your findings in the following format:

            {self.get_xml_review_comments_format(self.params['BUCKET'], self.params['AGENT_NAME'], self.agent_focus_area)} 

            If you are not able to comment due to any reason, be it an error, or you think the PR is good just give the review and root comments tag and don't put anything in it.
            Example:
            <review><comments></comments></review>

            8. Be thorough and err on the side of caution. It's better to flag a potential issue for further investigation than to miss a critical vulnerability.

            Keep in mind these important instructions when reviewing the code:
            -  Carefully analyze each change in the diff.
            -  Focus solely on security vulnerabilities as outlined above.
            -  Do not provide appreciation comments or positive feedback.
            -  Do not change the provided bucket name.
            -  Consider the context provided by contextually related code snippets.
            - For each finding or improvement, create a separate <comment> block within the <comments> section.
            -  If you find nothing to improve the PR, there should be no <comment> tags inside <comments> tag. Don't say anything other than identified issues/improvements. If no issue is identified, don't say anything.
            -  Ensure that your comments are clear, concise, and actionable.
            -  Provide specific line numbers and file paths for each finding.
            -  Assign appropriate confidence scores based on your certainty of the findings or improvements.
            -  Do not repeat similar comments for multiple instances of the same issue.
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
            -   Provide the exact, correct bucket name relevant to the issue. Ensure that the value is never left as a placeholder like "$BUCKET".
        """

        if self.params.get("CUSTOM_PROMPT"):
            user_message = f"{user_message}\n{CUSTOM_PROMPT_INSTRUCTIONS}\n{self.params['CUSTOM_PROMPT']}"

        return UserAndSystemMessages(user_message=user_message, system_message=system_message)
