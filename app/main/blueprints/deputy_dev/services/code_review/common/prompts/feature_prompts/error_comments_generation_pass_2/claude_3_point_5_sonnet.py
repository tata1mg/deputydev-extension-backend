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


class Claude3Point5ErrorCommentsGenerationPass2Prompt(BaseClaude3Point5SonnetCommentCreationPrompt):
    prompt_type = PromptFeatures.ERROR_COMMENTS_GENERATION_PASS_2.value
    prompt_category = PromptCategories.CODE_REVIEW.value

    def __init__(self, params: Dict[str, Any]) -> None:
        self.params = params
        self.agent_focus_area = AgentFocusArea.ERROR.value

    def get_prompt(self) -> UserAndSystemMessages:
        system_message = """
            You are a Principal Software Engineer expert at reviewing pull requests for errors. Your task is to
            review the comments made by a junior developer on a pull request, verifying their accuracy,
            relevancy, and correctness. You will then provide your own assessment, which may include adding more
            comments, updating existing ones, or deleting unnecessary ones.
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
            
            Here are the contextually relevant code snippets:
            <contextual_code_snippets>
            {self.params["CONTEXTUALLY_RELATED_CODE_SNIPPETS"]}
            </contextual_code_snippets>
            
            Here are the review comments made by the junior developer:
            <junior_developer_comments>
            {self.params["REVIEW_COMMENTS_BY_JUNIOR_DEVELOPER"]}
            </junior_developer_comments>
            </data>
            
            <guidelines>
            When reviewing the comments, consider the following guidelines for each type of error:
            
            1. Runtime Errors:
            <runtime_error_guidelines>
            - Potential issues that could cause the program to crash or behave unexpectedly
            during execution.
            </runtime_error_guidelines>
            
            2. Syntax Errors:
            <syntax_error_guidelines>
            - Check for missing semicolons, mismatched parentheses, or incorrect keyword usage.
            </syntax_error_guidelines>
            
            3. Semantic Errors:
            <semantic_error_guidelines>
            - Identify misuse of language features, such as improper type conversions or
            incorrect method calls.
            </semantic_error_guidelines>
            
            4. Edge Cases:
            <edge_cases_guidelines>
            - Consider extreme or unusual inputs that might cause unexpected behavior.
            </edge_cases_guidelines>
            
            Your task is to review each comment made by the junior developer and assess its accuracy, relevancy,
            and correctness. Consider this a level 2 review where you are verifying the junior developer's
            comments.
            
            For each comment:
            1. Determine if the comment accurately identifies an error or issue in the code.
            2. Check if the comment is relevant to the changes made in the pull request.
            3. Verify if the error type (Runtime, Syntax, Logical, Semantic, or Edge Case) is correctly
            identified.
            4. Assess if the proposed solution or corrective code (if any) is appropriate and effective.
            
            Based on your assessment:
            1. If a comment is accurate, relevant, and correct, include it in your final output.
            2. If a comment needs modification, update it with the correct information.
            3. If a comment is unnecessary or incorrect, omit it from your final output.
            4. If you identify additional errors or issues not mentioned by the junior developer, add new
            comments to address them.
            
            When adding or updating comments, ensure that you:
            1. Clearly describe the error or issue.
            2. Provide corrective code to remedy the issue when applicable.
            3. Specify the correct file path and line number for the comment.
            4. Assign an appropriate confidence score between 0.0 and 1.0.
            
            Important instructions:
            1. Create exactly one <comment> block for each error found.
            2. Only comment on aspects leading to the errors mentioned. 
            3. Do not comment on security, documentation, performance, or docstrings unless they directly relate
            to the specified categories and focus solely on major error-related issues that could lead to runtime failures or system instability.
            4. Ensure that each comment is relevant and actionable.
            5. Provide a confidence score for each comment, reflecting your certainty about the issue.
            6. Use the appropriate bucket label for each comment based on the category it falls under.
            7. Do not include appreciation comments, minor suggestions, or repeated issues.
            8. <pull_request_diff> contains the actual changes being made in this pull request, showing additions and deletions. 
                This is the primary focus for review comments. The diff shows:
                - Added lines (prefixed with +)
                - Removed lines (prefixed with -)
                - Context lines (no prefix)
                Only  Added lines and Removed lines  changes should receive direct review comments.
            9.  Comment should be part of code present in <pull_request_diff> and Use <contextually_related_code_snippets> 
            only for understanding impact of change. 
            10.  comment should not be on unchanged code unless directly impacted by the changes.
            11.  comment should not be duplicated for similar issues across different locations.
            12.  Before suggesting a comment or corrective code verify diligently that the suggestion is not already incorporated in the <pull_request_diff>.
            13. Do not change the provided bucket name.
            </guidelines>
            
            Next, receive the comments from <thinking> and remove comments which follow below criteria mentioned 
            in new_guidelines.
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
