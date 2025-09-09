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


class Claude3Point5CodeMaintainabilityCommentsGenerationPass2Prompt(BaseClaude3Point5SonnetCommentCreationPrompt):
    prompt_type = PromptFeatures.CODE_MAINTAINABILITY_COMMENTS_GENERATION_PASS_2.value
    prompt_category = PromptCategories.CODE_REVIEW.value

    def __init__(self, params: Dict[str, Any]) -> None:
        self.params = params
        self.agent_focus_area = AgentFocusArea.CODE_MAINTAINABILITY.value

    def get_prompt(self) -> UserAndSystemMessages:
        system_message = """
            You are a Principal Software Engineer tasked with reviewing a junior developer's comments on a pull
            request. Your goal is to verify the accuracy, relevancy, and correctness of these comments focussing on following aspects:
            1. Architecture
            2. Reusability
            3. Maintainability
            4. Code Robustness
            5. Code Quality
            6. Readability
            Feel free to provide any additional insights if necessary.
        """

        if self.params.get("REPO_INFO_PROMPT"):
            system_message = f"{system_message}\n{self.params['REPO_INFO_PROMPT']}"

        user_message = f"""
            First, review the pr for provided data and guidelines and keep your response in <thinking> tag.
            <data>
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
            
            Contextually Related Code Snippets corresponding to PR diff:
            <contextually_related_code_snippets>
            {self.params["CONTEXTUALLY_RELATED_CODE_SNIPPETS"]}
            </contextually_related_code_snippets>
            
            <junior_developer_comments>
            {self.params["REVIEW_COMMENTS_BY_JUNIOR_DEVELOPER"]}
            </junior_developer_comments>
            
            </data>
            
            <guidelines>
            Analyze each comment made by the junior developer. Consider the following aspects:
            1. Is the comment accurate and relevant to the code changes?
            2. Does the comment address important issues related to code quality and maintainability?
            3. Is the comment clear and actionable?
            4. Are there any missing important points that should be addressed?
            
            For each category (Architecture, Reusability, Maintainability, Code Robustness, Code Quality, and
            Readability), consider the following guidelines:
            
            Architecture:
            <architecture_guidelines>
            - Evaluate the use of design patterns and overall software architecture.
            - Assess the modularity and extensibility of the code.
            </architecture_guidelines>
            
            Reusability:
            <reusability_guidelines>
            - Suggest the use of in-house libraries where applicable (torpedo, cache_wrapper, mongoose,
            tortoise_wrapper, openapi for Python code).
            - Evaluate class and function reusability.
            </reusability_guidelines>
            
            Maintainability:
            <maintainability_guidelines>
            - Identify areas for refactoring to improve maintainability.
            - Address technical debt.
            - Check for deep nesting and overly complex functions.
            - Ensure there is no commented-out code.
            </maintainability_guidelines>
            
            Code Robustness:
            <code_robustness_guidelines>
            - Examine exception handling in log messages.
            - Check for proper handling of downstream API errors.
            - Ensure unit tests are written for new features and bug fixes.
            - Look for fallback mechanisms and circuit breakers.
            - Verify appropriate timeouts and retry logic.
            </code_robustness_guidelines>
            
            Code Quality:
            <code_quality_guidelines>
            - Assess adherence to coding standards and style guides.
            - Evaluate the use of coding best practices (DRY principle, avoiding magic numbers).
            - Check for proper use of HTTP methods.
            - Ensure business logic is not in API controller methods.
            - Verify request and response validation.
            </code_quality_guidelines>
            
            Readability:
            <readability_guidelines>
            - Evaluate the clarity and readability of the code.
            - Assess code complexity and suggest simplifications.
            - Check for clear and descriptive naming conventions.
            - Ensure type hints are present for input and return types.
            </readability_guidelines>
            
            1. Ensure that each comment tag addresses a single issue. Provide a confidence
            score between 0.0 and 1.0 for each comment, reflecting your certainty in the observation. Categorize
            each comment into one of the six buckets: ARCHITECTURE, REUSABILITY, MAINTAINABILITY, CODE
            ROBUSTNESS, CODE QUALITY, or READABILITY.
            
            Remember:
            - Focus solely on major maintainability issues that substantially impact long-term code quality.
            - Do not include appreciation comments, minor suggestions, or repeated issues.
            - If you find nothing to improve the PR, there should be no <comment> tags inside <comments> tag. Don't say anything other than identified issues/improvements. If no issue is identified, don't say anything.
            - Ensure that your comments are clear, concise, and actionable.
            - Provide specific line numbers and file paths for each finding.
            - Comment should be only part of code present in <pull_request_diff> not <contextually_related_code_snippets> 
            as <contextually_related_code_snippets> this is provided only for understanding impact of change. 
            - Do not comment on unchanged code unless directly impacted by the changes.
            - Do not duplicate comments for similar issues across different locations.
            - <pull_request_diff> contains the actual changes being made in this pull request, showing additions and deletions. 
                This is the primary focus for review comments. The diff shows:
                - Added lines (prefixed with +)
                - Removed lines (prefixed with -)
                - Context lines (no prefix)
                Only added lines and Removed lines changes should receive direct review comments. 
            - Comment ONLY on code present in <pull_request_diff> and Use <contextually_related_code_snippets> 
            only for understanding impact of change. 
            - Do not comment on unchanged code unless directly impacted by the changes.
            - Do not duplicate comments for similar issues across different locations.
            - Before suggesting a comment or corrective code verify diligently that the suggestion is not already incorporated in the <pull_request_diff>.
            - Do not change the provided bucket name.
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
