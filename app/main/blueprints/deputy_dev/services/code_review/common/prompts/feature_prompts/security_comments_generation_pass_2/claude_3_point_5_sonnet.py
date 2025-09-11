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


class Claude3Point5SecurityCommentsGenerationPass2Prompt(BaseClaude3Point5SonnetCommentCreationPrompt):
    prompt_type = PromptFeatures.SECURITY_COMMENTS_GENERATION_PASS_2.value
    prompt_category = PromptCategories.CODE_REVIEW.value
    disable_tools = True

    def __init__(self, params: Dict[str, Any]) -> None:
        self.params = params
        self.agent_focus_area = AgentFocusArea.SECURITY.value

    def get_prompt(self) -> UserAndSystemMessages:
        system_message = """
            You are a highly skilled code security expert tasked with reviewing a pull request for potential security
            issues and vulnerabilities. Your goal is to provide a thorough and accurate security review,
            improving upon an initial analysis.
        """
        if self.params.get("REPO_INFO_PROMPT"):
            system_message = f"{system_message}\n{self.params['REPO_INFO_PROMPT']}"

        user_message = f"""
            First, review the pr for provided data and guidelines and keep your response in <thinking> tag.
            <data>
            <pull_request_title>
            {self.params["PULL_REQUEST_TITLE"]}
            </pull_request_title>
            
            <pull_request_description>
            {self.params["PULL_REQUEST_DESCRIPTION"]}
            </pull_request_description>
            
            <pull_request_diff>
            {self.params["PULL_REQUEST_DIFF"]}
            </pull_request_diff>
            
            <junior_developer_comments>
            {self.params["REVIEW_COMMENTS_BY_JUNIOR_DEVELOPER"]}
            </junior_developer_comments>
            </data>
            
            <guidelines>
            Conduct a comprehensive security review of the code changes, focusing on the following aspects:
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

            Be thorough and err on the side of caution. It's better to flag a potential issue for further investigation than to miss a critical vulnerability.

            Keep in mind these important instructions when reviewing the code:
            1. Carefully analyze each change in the diff.
            2. Focus solely on major performance issues that could substantially impact system efficiency.
            3. Do not include appreciation comments, minor suggestions, or repeated issues.
            4. Consider the context provided by contextually related code snippets.
            5. For each finding or improvement, create a separate <comment> block within the <comments> section.
            6. If you find nothing to improve the PR, there should be no <comment> tags inside <comments> tag. Don't say anything other than identified issues/improvements. If no issue is identified, don't say anything.
            7. Ensure that your comments are clear, concise, and actionable.
            8. Provide specific line numbers and file paths for each finding.
            9. Assign appropriate confidence scores based on your certainty of the findings or improvements.
            10. <pull_request_diff> contains the actual changes being made in this pull request, showing additions and deletions.
                This is the primary focus for review comments. The diff shows:
                - Added lines (prefixed with +)
                - Removed lines (prefixed with -)
                - Context lines (no prefix)
                Only added lines and Removed lines changes should receive direct review comments.
            11.  Comment should be part of code present in <pull_request_diff> and Use <contextually_related_code_snippets>
            only for understanding impact of change.
            12.  comment should not be on unchanged code unless directly impacted by the changes.
            13.  comment should not be duplicated for similar issues across different locations.
            14.  Before suggesting a comment or corrective code verify diligently that the suggestion is not already incorporated in the <pull_request_diff>.
            15.  Do not change the provided bucket name.

            </guidelines>

            Next, receive the comments from <thinking> and remove comments which follow below criteria mentioned
            in new_guidelines.
            <new_guidelines>
            1. If any comment is already catered.
            2. If comment is not part of added and Removed lines.
            3. If any comment reflects appreciation.
            4. If comment is not part of PR diff.
            </new_guidelines>

           Once you have gathered all necessary context and are confident in your findings, call the
            "parse_final_response" tool with your review in XML format:

            If you are not able to comment due to any reason, be it an error, or you think the PR is good just give the review and root comments tag and don't put anything in it.
            Example:
            <review><comments></comments></review>
        """

        if self.params.get("CUSTOM_PROMPT"):
            user_message = f"{user_message}\n{CUSTOM_PROMPT_INSTRUCTIONS}\n{self.params['CUSTOM_PROMPT']}"

        return UserAndSystemMessages(user_message=user_message, system_message=system_message)
