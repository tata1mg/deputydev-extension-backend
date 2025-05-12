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


class Claude3Point5ErrorCommentsGenerationPass1Prompt(BaseClaude3Point5SonnetCommentCreationPrompt):
    prompt_type = PromptFeatures.ERROR_COMMENTS_GENERATION_PASS_1.value
    prompt_category = PromptCategories.CODE_REVIEW.value

    def __init__(self, params: Dict[str, Any]):
        self.params = params
        self.agent_focus_area = AgentFocusArea.ERROR.value

    def get_prompt(self) -> UserAndSystemMessages:
        system_message = """
            You are a senior developer tasked with reviewing a pull request for errors. Your goal is to identify
            and comment on various types of errors in the code. Focus solely on finding and reporting errors,
            not on other aspects of code review.
        """

        if self.params.get("REPO_INFO_PROMPT"):
            system_message = f"{system_message}\n{self.params['REPO_INFO_PROMPT']}"

        user_message = f"""
            Here's the information about the pull request:

            <pull_request_title>
            {self.params["PULL_REQUEST_TITLE"]}
            </pull_request_title>

            <pull_request_description>
            {self.params["PULL_REQUEST_DESCRIPTION"]}
            </pull_request_description>

            Now, examine the following diff and related code snippets:

            <pull_request_diff>
            {self.params["PULL_REQUEST_DIFF"]}
            </pull_request_diff>

            <contextually_related_code_snippets>
            {self.params["CONTEXTUALLY_RELATED_CODE_SNIPPETS"]}
            </contextually_related_code_snippets>

            Focus on identifying the following types of errors:

            1. Runtime errors
            2. Syntax errors
            3. Logical errors
            4. Semantic errors
            5. Edge cases
            6. Unhandled exceptions

            Guidelines for identifying each error type:
            1. Runtime Errors:
            <runtime_error_guidelines>
            - Potential issues that could cause the program to crash or behave unexpectedly
            during execution.
            </runtime_error_guidelines>

            2. Syntax Errors:
            <syntax_error_guidelines>
            - Check for missing semicolons, mismatched parentheses, or incorrect keyword usage.
            </syntax_error_guidelines>

            3. Logical Errors:
            <logical_error_guidelines>
            - Analyze the code's flow and algorithms for incorrect calculations or faulty
            conditionals.
            </logical_error_guidelines>

            4. Semantic Errors:
            <semantic_error_guidelines>
            - Identify misuse of language features, such as improper type conversions or
            incorrect method calls.
            </semantic_error_guidelines>

            5. Edge Cases:
            <edge_cases_guidelines>
            - Consider extreme or unusual inputs that might cause unexpected behavior.
            </edge_cases_guidelines>

            6. Unhandled exceptions:
            <unhandled_exceptions>
            - Check for Unhandled exceptions in critical code paths.
            </unhandled_exceptions> 

            Analyze the code thoroughly and provide your feedback in the following XML format:

            {self.get_xml_review_comments_format(self.params["BUCKET"], self.params["AGENT_NAME"], self.agent_focus_area)} 

            If you are not able to comment due to any reason, be it an error, or you think the PR is good just give the review and root comments tag and don't put anything in it.
            Example:
            <review><comments></comments></review>

            Important: Focus exclusively on identifying and reporting errors. Do not comment on other aspects of
            code review such as security, documentation, performance, or docstrings unless they directly relate
            to an error.

            When reviewing the code:
            -  Carefully analyze each change in the diff.
            -  Focus solely on major error-related issues as outlined above.
            -  Do not comment on minor issues or hypothetical edge cases
            -  Do not provide appreciation comments or positive feedback.
            - Do not change the provided bucket name.
            -  Consider the context provided by related code snippets.
            -  For each error found, create a separate <comment> block within the <comments> section.
            -  Ensure that your comments are clear, concise, and actionable.
            -  Provide specific line numbers and file paths for each error.
            -  Assign appropriate confidence scores based on your certainty of the error.
            - Do not repeat similar comments for multiple instances of the same issue.
            - <pull_request_diff> contains the actual changes being made in this pull request, showing additions and deletions. 
                This is the primary focus for review comments. The diff shows:
                - Added lines (prefixed with +)
                - Removed lines (prefixed with -)
                - Context lines (no prefix)
                Only  Added lines and Removed lines  changes should receive direct review comments.
            -  Comment ONLY on code present in <pull_request_diff> and Use <contextually_related_code_snippets> 
            only for understanding impact of change. 
            -   Do not comment on unchanged code unless directly impacted by the changes.
            -   Do not duplicate comments for similar issues across different locations.
            -   If you are suggesting any comment that is already catered please don't include those comment in response.
            -   Provide the exact, correct bucket name relevant to the issue. Ensure that the value is never left as a placeholder like "$BUCKET".

            Remember to maintain a professional and constructive tone in your comments. Your goal is to help
            improve the code quality by identifying and explaining errors accurately.
        """

        if self.params.get("CUSTOM_PROMPT"):
            user_message = f"{user_message}\n{CUSTOM_PROMPT_INSTRUCTIONS}\n{self.params['CUSTOM_PROMPT']}"

        return UserAndSystemMessages(user_message=user_message, system_message=system_message)
