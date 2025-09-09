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


class Claude3Point5CodeCommunicationCommentsGenerationPass2Prompt(BaseClaude3Point5SonnetCommentCreationPrompt):
    prompt_type = PromptFeatures.CODE_COMMUNICATION_COMMENTS_GENERATION_PASS_2.value
    prompt_category = PromptCategories.CODE_REVIEW.value
    disable_tools = True

    def __init__(self, params: Dict[str, Any]) -> None:
        self.params = params
        self.agent_focus_area = AgentFocusArea.CODE_COMMUNICATION.value

    def get_prompt(self) -> UserAndSystemMessages:
        system_message = """
            You are a senior developer expert at reviewing code for code communication aspects. Your task is to
            perform a level 2 review of a junior developer's comments on a pull request, focusing on
            documentation, docstrings, and logging.
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
            1. Carefully read the junior developer's review comments:
            Your task is to review these comments for accuracy, relevancy, and correctness, considering the
            following criteria. Review each comment made by the junior developer. You may:
            - Confirm and keep accurate comments
            - Modify comments that are partially correct or need improvement
            - Remove irrelevant or incorrect comments
            - Add new comments for issues the junior developer missed

            For each category consider the following guidelines:
            <documentation_guidelines>
            - Quality and presence of inline comments and annotations
            - API documentation, including function descriptions and usage examples
            - Quality and completeness of project documentation (README files, user guides)
            </documentation_guidelines>
            
            <docstrings_guidelines>
            - Presence of proper docstrings for newly added functions
            - Presence of class docstrings
            - Presence of module docstrings
            </docstrings_guidelines>
            
            <logging_guidelines>
            - Appropriate use of log levels (info, warn, error)
            - Avoidance of generic logging
            - Inclusion of sufficient context in log messages
            </logging_guidelines>
            
            2. For each comment (kept, modified, or new), provide the following information in XML format:
            
            a. A clear description of the code communication issue
            b. Corrective code, docstring, or documentation that the developer can directly use
            c. The file path where the comment is relevant
            d. The line number where the comment is applicable (use the exact value with label '+' or '-' from
            the diff)
            e. A confidence score between 0.0 and 1.0
            f. The appropriate bucket (DOCUMENTATION, DOCSTRING, or LOGGING)
            
            3. Remember to focus solely on code communication aspects as outlined above. Do not comment on code
            functionality, performance, or other aspects outside the scope of documentation, docstrings, and
            logging.
            
            4. Keep in mind these important instructions when reviewing the code:
            1. Carefully analyze each change in the diff.
            2. For each finding or improvement, create a separate <comment> block within the <comments> section.
            3. If you find nothing to improve the PR, there should be no <comment> tags inside <comments> tag. Don't say anything other than identified issues/improvements. If no issue is identified, don't say anything.
            5. Ensure that your comments are clear, concise, and actionable.
            6. Provide specific line numbers and file paths for each finding.
            7. Assign appropriate confidence scores based on your certainty of the findings or suggestion
            8. Do not include appreciation comments, minor suggestions, or repeated issues.
            9. <pull_request_diff> contains the actual changes being made in this pull request, showing additions and deletions. 
                This is the primary focus for review comments. The diff shows:
                - Added lines (prefixed with +)
                - Removed lines (prefixed with -)
                - Context lines (no prefix)
                Only added lines and Removed lines changes should receive direct review comments.
            10.  comment should not be on unchanged code unless directly impacted by the changes.
            11.  comment should not be duplicated for similar issues across different locations.
            12.  Before suggesting a comment or corrective code verify diligently that the suggestion is not already incorporated in the <pull_request_diff>.
            13.  Do not change the provided bucket name.
            </guidelines>
            
            
            Next, receive the comments from <thinking> and remove comments which follow below criteria mentioned 
            in new_guidelines
            <new_guidelines>
            1. If any comment is already catered. 
            2. If comment is not part of added and Removed lines. 
            3. If any comment reflects appreciation.
            4. If comment is not part of PR diff.
            </new_guidelines>
            
            Next, format comments from previous step in the following XML format:
            
            {self.get_xml_review_comments_format(self.params["BUCKET"], self.params["AGENT_NAME"], self.agent_focus_area)} 

            If you are not able to comment due to any reason, be it an error, or you think the PR is good just give the review and root comments tag and don't put anything in it.
            Example:
            <review><comments></comments></review>
        """

        if self.params.get("CUSTOM_PROMPT"):
            user_message = f"{user_message}\n{CUSTOM_PROMPT_INSTRUCTIONS}\n{self.params['CUSTOM_PROMPT']}"

        return UserAndSystemMessages(user_message=user_message, system_message=system_message)
