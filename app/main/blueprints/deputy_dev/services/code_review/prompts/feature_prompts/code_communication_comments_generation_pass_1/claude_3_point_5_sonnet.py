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


class Claude3Point5CodeCommunicationCommentsGenerationPass1Prompt(BaseClaude3Point5SonnetCommentCreationPrompt):
    prompt_type = PromptFeatures.CODE_COMMUNICATION_COMMENTS_GENERATION_PASS_1.value
    prompt_category = PromptCategories.CODE_REVIEW.value

    def __init__(self, params: Dict[str, Any]):
        self.params = params
        self.agent_focus_area = AgentFocusArea.CODE_COMMUNICATION.value

    def get_prompt(self) -> UserAndSystemMessages:
        system_message = """
            You are a code reviewer tasked with evaluating a pull request specifically for code communication
            aspects. Your focus will be on documentation, docstrings, and logging. You will be provided with the
            pull request title, description, and the PR's diff (Output of `git diff` command)
        """

        if self.params.get("REPO_INFO_PROMPT"):
            system_message = f"{system_message}\n{self.params['REPO_INFO_PROMPT']}"

        user_message = f"""
            1. Here's the information for the pull request you need to review:
            
            Pull Request Title:
            <pull_request_title>
            {self.params["PULL_REQUEST_TITLE"]}
            </pull_request_title>
            
            Pull Request Description:
            <pull_request_description>
            {self.params["PULL_REQUEST_DESCRIPTION"]}
            </pull_request_description>
            
            Pull Request Diff:
            <pull_request_diff>
            {self.params["PULL_REQUEST_DIFF"]}
            </pull_request_diff>
            
            2. Next, please review the pull request focusing on the following aspects. Consider each of them as a bucket:
            
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
            
            3. For each bucket (Documentation, Docstrings, and Logging), provide your comments to be made on PR for improvements.
            Use the following format for your review comments:
            
            {self.get_xml_review_comments_format(self.params["BUCKET"], self.params["AGENT_NAME"], self.agent_focus_area)}            

            If you are not able to comment due to any reason, be it an error, or you think the PR is good just give the review and root comments tag and don't put anything in it.
            Example:
            <review><comments></comments></review>

            4. Remember to focus solely on code communication aspects as outlined above. Do not comment on code
            functionality, performance, or other aspects outside the scope of documentation, docstrings, and
            logging.
            
            Keep in mind these important instructions when reviewing the code:
            - Focus solely on major code communication issues as outlined above.
            - Carefully analyze each change in the diff.
            - For each finding or improvement, create a separate <comment> block within the <comments> section.
            - If you find nothing to improve the PR, there should be no <comment> tags inside <comments> tag. Don't say anything other than identified issues/improvements. If no issue is identified, don't say anything.
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
        """

        if self.params.get("CUSTOM_PROMPT"):
            user_message = f"{user_message}\n{CUSTOM_PROMPT_INSTRUCTIONS}\n{self.params['CUSTOM_PROMPT']}"

        return UserAndSystemMessages(user_message=user_message, system_message=system_message)
