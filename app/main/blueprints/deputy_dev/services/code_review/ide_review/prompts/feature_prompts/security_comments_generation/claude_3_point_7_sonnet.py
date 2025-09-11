from typing import Any, Dict

from deputydev_core.llm_handler.dataclasses.main import UserAndSystemMessages
from deputydev_core.llm_handler.models.dto.message_thread_dto import LLModels

from app.backend_common.dataclasses.dataclasses import PromptCategories
from app.main.blueprints.deputy_dev.constants.constants import (
    CUSTOM_PROMPT_INSTRUCTIONS,
    AgentFocusArea,
)
from app.main.blueprints.deputy_dev.services.code_review.common.prompts.dataclasses.main import PromptFeatures
from app.main.blueprints.deputy_dev.services.code_review.ide_review.prompts.base_prompts.claude_3_point_5_sonnet_comment_creation import (
    BaseClaude3Point5SonnetCommentCreationPrompt,
)


class Claude3Point7SecurityCommentsGenerationPrompt(BaseClaude3Point5SonnetCommentCreationPrompt):
    prompt_type = PromptFeatures.SECURITY_COMMENTS_GENERATION.value
    prompt_category = PromptCategories.CODE_REVIEW.value
    disable_tools = True
    model_name = LLModels.CLAUDE_3_POINT_7_SONNET

    def __init__(self, params: Dict[str, Any]) -> None:
        self.params = params
        self.agent_focus_area = AgentFocusArea.SECURITY.value

    def get_system_prompt(self) -> str:
        return self.get_tools_configurable_system_message(self.params)

    def get_prompt(self) -> UserAndSystemMessages:
        system_message = self.get_system_prompt()

        cached_message = self.get_user_cached_message_template(self.params)
        user_message = """
            You are specifically reviewing this pull request as a SECURITY ENGINEER.
            Your focus is on identifying security vulnerabilities and potential security risks in the code changes.

            <security_review_approach>
            Unlike general code reviews, security reviews require a targeted approach:

            1. ANALYZE THE DIFF FIRST: Begin by thoroughly examining the PR diff for obvious security issues such as:
              - Hardcoded credentials
              - Insecure cryptographic implementations
              - Injection vulnerabilities in new/modified code
              - Authentication/authorization bypasses
              - And any other critical application security issues.
            </security_review_approach>


            Instructions to Review: 
            - For each security issue or vulnerability you identify:
                a. Describe the issue, it's potential impact and its severity. This will be a comment on the PR.
                b. Corrected code - Rewrite the code snippet. How the code should be written ideally.
                c. File path - path of the file on which comment is being made
                d. line number – the line on which the comment is relevant. Extract this from the `<>` block at the start of each code snippet in the input. Return exactly the value labeled with “+”. Comments must be made only on added lines (“+”).
                e. Confidence score - floating point confidence score of the comment between 0.0 to 1.0

            - Once you have gathered all necessary context and are confident in your findings, call the
                "parse_final_response" tool with your review comments:

            - Be thorough and err on the side of caution. It's better to flag a potential issue for further investigation than to miss a critical vulnerability.


                Keep in mind these important instructions when reviewing the code:
                -  Carefully analyze each change in the diff.
                - If you find something like certain change can have cascading effect in some other files too, Provide the exact file path, line number and the code snippet affected by the change.
                -  Focus solely on security vulnerabilities as outlined above.
                -  Do not provide appreciation comments or positive feedback.
                -  Do not change the provided bucket name.
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
                -  Comment ONLY on code present in <pull_request_diff> 
                only for understanding impact of change. 
                -   Do not comment on unchanged code unless directly impacted by the changes.
                -   Do not duplicate comments for similar issues across different locations.
                -   If you are suggesting any comment that is already catered please don't include those comment in response.
                -   Provide the exact, correct bucket name relevant to the issue. Ensure that the value is never left as a placeholder like "$BUCKET".
                - Before suggesting a comment or corrective code verify diligently that the suggestion is not already incorporated in the <pull_request_diff>.
            """

        if self.params.get("CUSTOM_PROMPT"):
            user_message = f"{user_message}\n{CUSTOM_PROMPT_INSTRUCTIONS}\n{self.params['CUSTOM_PROMPT']}"

        return UserAndSystemMessages(
            user_message=user_message, system_message=system_message, cached_message=cached_message
        )
