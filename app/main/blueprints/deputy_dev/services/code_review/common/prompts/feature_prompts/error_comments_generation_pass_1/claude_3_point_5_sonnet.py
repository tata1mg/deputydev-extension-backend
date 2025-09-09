from typing import Any, Dict

from app.backend_common.dataclasses.dataclasses import PromptCategories
from app.main.blueprints.deputy_dev.constants.constants import (
    CUSTOM_PROMPT_INSTRUCTIONS,
    AgentFocusArea,
)
from deputydev_core.llm_handler.dataclasses.main import UserAndSystemMessages

from ...base_prompts.claude_3_point_5_sonnet_comment_creation import (
    BaseClaude3Point5SonnetCommentCreationPrompt,
)
from ...dataclasses.main import PromptFeatures


class Claude3Point5ErrorCommentsGenerationPass1Prompt(BaseClaude3Point5SonnetCommentCreationPrompt):
    prompt_type = PromptFeatures.ERROR_COMMENTS_GENERATION_PASS_1.value
    prompt_category = PromptCategories.CODE_REVIEW.value

    def __init__(self, params: Dict[str, Any]) -> None:
        self.params = params
        self.agent_focus_area = AgentFocusArea.ERROR.value

    def get_system_prompt(self) -> str:
        return self.get_tools_specific_system_message(self.params)

    def get_prompt(self) -> UserAndSystemMessages:
        system_message = self.get_system_prompt()

        cached_message = self.get_user_cached_message_template(self.params)

        user_message = """
            You are specifically reviewing this pull request as an ERROR DETECTION ENGINEER.
            Your goal is to identify and comment on various types of errors in the code.
            Focus solely on finding and reporting errors, not on other aspects of code review.
            
            Instructions to Review: 

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


            Important: Focus exclusively on identifying and reporting errors. Do not comment on other aspects of
            code review such as security, documentation, performance, or docstrings unless they directly relate
            to an error.

            When reviewing the code:
            -  Carefully analyze each change in the diff.
            - If you find something like certain change can have cascading effect in some other files too, Provide the exact file path, line number and the code snippet affected by the change.
            -  Focus solely on major error-related issues as outlined above.
            -  Do not comment on minor issues or hypothetical edge cases
            -  Do not provide appreciation comments or positive feedback.
            - Do not change the provided bucket name.
            -  Consider the context provided by related code snippets.
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
            -  Comment ONLY on code present in <pull_request_diff> 
            only for understanding impact of change. 
            -   Do not comment on unchanged code unless directly impacted by the changes.
            -   Do not duplicate comments for similar issues across different locations.
            -   If you are suggesting any comment that is already catered please don't include those comment in response.
            -   Provide the exact, correct bucket name relevant to the issue. Ensure that the value is never left as a placeholder like "$BUCKET".
            -  Use all the required tools if you need to fetch some piece of code based on it. 
            - Before suggesting a comment or corrective code verify diligently that the suggestion is not already incorporated in the <pull_request_diff>.

            Remember to maintain a professional and constructive tone in your comments. Your goal is to help
            improve the code quality by identifying and explaining errors accurately.
        """
        if self.params.get("final_breach") == "true":
            return self.get_finalize_iteration_breached_prompt()
        if self.params.get("CUSTOM_PROMPT"):
            user_message = f"{user_message}\n{CUSTOM_PROMPT_INSTRUCTIONS}\n{self.params['CUSTOM_PROMPT']}"

        return UserAndSystemMessages(
            user_message=user_message, system_message=system_message, cached_message=cached_message
        )

    def get_finalize_iteration_breached_prompt(self) -> UserAndSystemMessages:
        user_message = self.get_force_finalize_user_message()
        system_message = self.get_system_prompt()
        return UserAndSystemMessages(user_message=user_message, system_message=system_message)
