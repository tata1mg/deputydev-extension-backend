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


class Claude3Point5BusinessLogicValidationCommentsGenerationPass2Prompt(BaseClaude3Point5SonnetCommentCreationPrompt):
    prompt_type = PromptFeatures.BUSINESS_LOGIC_VALIDATION_COMMENTS_GENERATION_PASS_2.value
    prompt_category = PromptCategories.CODE_REVIEW.value

    def __init__(self, params: Dict[str, Any]) -> None:
        self.params = params
        self.agent_focus_area = AgentFocusArea.BUSINESS_LOGIC_VALIDATION.value

    def get_prompt(self) -> UserAndSystemMessages:
        system_message = """
            You are a Principal Software Engineer tasked with reviewing a pull request for functional
            correctness, focusing specifically on business logic alignment with given requirements. You will be
            conducting a level 2 review, verifying and potentially modifying comments made by a junior
            developer.
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
            
            <contextually_related_code_snippets>
            {self.params["CONTEXTUALLY_RELATED_CODE_SNIPPETS"]}
            </contextually_related_code_snippets>
            
            <user_story>
            {self.params["USER_STORY"]}
            </user_story>
        
            <product_research_document>
            {self.params["PRODUCT_RESEARCH_DOCUMENT"]}
            </product_research_document>
            
            <junior_developer_comments>
            {self.params["REVIEW_COMMENTS_BY_JUNIOR_DEVELOPER"]}
            </junior_developer_comments>
            
            </data>
            <guidelines>
            Your task is to review the changes made in the pull request and determine if they align with the
            given requirements. You should verify the accuracy, relevancy, and correctness of the junior
            developer's comments. You may add new comments, update existing ones, or remove unnecessary
            comments.
            When reviewing, please adhere to the following guidelines:
            1. Focus solely on business logic validation. Do not comment on other aspects such as security,
            documentation, performance, or docstrings.
            2. Ensure each comment is relevant to the changes made in the pull request and the given
            requirements.
            3. Provide clear and concise descriptions of any issues found.
            4. When suggesting corrective code, ensure it directly addresses the issue and can be easily
            implemented by the developer.
            5. Assign an appropriate confidence score to each comment based on your certainty of the issue.
            6. Use the exact line numbers from the diff when referencing specific lines of code.
            7. Always set the bucket value to "USER_STORY" as this is a business logic validation review.
            8. Keep only comments that identify critical misalignments with business requirements.
            9. Remove any appreciation comments or general observations.
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
            14. Before suggesting a comment or corrective code verify diligently that the suggestion is not already incorporated in the <pull_request_diff>.
            15. Do not change the provided bucket name.
            
            Remember, your primary goal is to ensure that the changes in the pull request accurately implement
            the requirements specified in the user story and product research document. Do not get sidetracked
            by other aspects of code review that are not related to business logic correctness. 
            Note: Need not to do the appreciation comments for the things that are done correctly.
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
