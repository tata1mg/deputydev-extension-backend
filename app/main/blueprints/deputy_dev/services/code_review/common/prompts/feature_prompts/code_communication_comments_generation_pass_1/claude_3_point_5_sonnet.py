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


class Claude3Point5CodeCommunicationCommentsGenerationPass1Prompt(BaseClaude3Point5SonnetCommentCreationPrompt):
    prompt_type = PromptFeatures.CODE_COMMUNICATION_COMMENTS_GENERATION_PASS_1.value
    prompt_category = PromptCategories.CODE_REVIEW.value
    disable_tools = True

    def __init__(self, params: Dict[str, Any]) -> None:
        self.params = params
        self.agent_focus_area = AgentFocusArea.CODE_COMMUNICATION.value

    def get_system_prompt(self) -> str:
        return self.get_tools_configurable_system_message(self.params)

    def get_prompt(self) -> UserAndSystemMessages:
        system_message = self.get_system_prompt()

        cached_message = self.get_user_cached_message_template(self.params)

        user_message = """
            You are specifically reviewing this pull request as a DOCUMENTATION & COMMUNICATION ENGINEER.
            Your focus is on code communication aspects including documentation, docstrings, and logging.
        
            Instructions to Review: 
            - Review the pull request focusing on the following aspects. Consider each of them as a bucket:
            
            <documentation_guidelines>
            - Evaluate the quality and presence of inline comments and annotations in the code.
            - Check for API documentation, including function descriptions and usage examples.
            - Assess the quality and completeness of project documentation such as README files and user guides.
            </documentation_guidelines>
            
            <docstrings_guidelines>
            - Verify that proper docstrings are present for each newly added function.
            - Check if class docstrings are missing.
            - Ensure that module docstrings are present.
            </docstrings_guidelines>
            
            <logging_guidelines>
            - Review the use of log levels (e.g., info, warn, error) in log messages.
            - Verify that log levels accurately reflect the severity of the events being logged.
            - Check for generic logging and examine if the log messages include sufficient information for
            understanding the context of the logged events.
            </logging_guidelines>
    
        
            - Remember to focus solely on code communication aspects as outlined above. Do not comment on code
            functionality, performance, or other aspects outside the scope of documentation, docstrings, and
            logging.
            
            
            Keep in mind these important instructions when reviewing the code:
            - Focus solely on major code communication issues as outlined above.
            - If you find something like certain change can have cascading effect in some other files too, Provide the exact file path, line number and the code snippet affected by the change.
            - Carefully analyze each change in the diff.
            - Ensure that your comments are clear, concise, and actionable.
            - Provide specific line numbers and file paths for each finding.
            - Assign appropriate confidence scores based on your certainty of the findings or suggestion
            - Do not provide appreciation comments or positive feedback.
            - Do not change the provided bucket name.
            - <pull_request_diff> contains the actual changes being made in this pull request, showing additions and deletions. 
                This is the primary focus for review comments. The diff shows:
                - Added lines (prefixed with +)
                - Removed lines (prefixed with -)
                - Context lines (no prefix)
                Only added lines and Removed lines changes should receive direct review comments.
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
