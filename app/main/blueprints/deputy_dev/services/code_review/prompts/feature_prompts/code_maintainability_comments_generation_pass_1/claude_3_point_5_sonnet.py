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


class Claude3Point5CodeMaintainabilityCommentsGenerationPass1Prompt(BaseClaude3Point5SonnetCommentCreationPrompt):
    prompt_type = PromptFeatures.CODE_MAINTAINABILITY_COMMENTS_GENERATION_PASS_1.value
    prompt_category = PromptCategories.CODE_REVIEW.value

    def __init__(self, params: Dict[str, Any]):
        self.params = params
        self.agent_focus_area = AgentFocusArea.CODE_MAINTAINABILITY.value

    def get_prompt(self) -> UserAndSystemMessages:
        system_message = """
            You are a senior developer tasked with reviewing a pull request for code quality and
            maintainability. Your goal is to provide detailed feedback on the following aspects:
            
            1. Architecture
            2. Reusability
            3. Maintainability
            4. Code Robustness
            5. Code Quality
            6. Readability
        """

        if self.params.get("REPO_INFO_PROMPT"):
            system_message = f"{system_message}\n{self.params['REPO_INFO_PROMPT']}"

        user_message = f"""
            Here is the information for the pull request you need to review:
            
            Pull Request Title: 
            <pull_request_title>
            {self.params['PULL_REQUEST_TITLE']}
            </pull_request_title>
            
            Pull Request Description:
            <pull_request_description>
            {self.params['PULL_REQUEST_DESCRIPTION']}
            </pull_request_description>
            
            Pull Request Diff:
            <pull_request_diff>
            {self.params['PULL_REQUEST_DIFF']}
            </pull_request_diff>
            
            Contextually Related Code Snippets corresponding to PR diff:
            Additional code snippets that contain related files, dependent code but are not PR diff.
            <contextually_related_code_snippets>
            {self.params['CONTEXTUALLY_RELATED_CODE_SNIPPETS']}
            </contextually_related_code_snippets>
            
            Review the code carefully, focusing on the following guidelines for each category:
            
            1. Architecture:
            <architecture_guidelines>
            - Major violations of SOLID principles.
            - Design Patterns: Evaluate the use of design patterns and overall software architecture.
            - Modularity: Ensure code is modular for component reusability.
            - Extensibility: Assess the extensibility of the codebase and its components.
            </architecture_guidelines>
            
            2. Reusability:
            <reusability_guidelines>
            - In-house Libraries: Suggest using in-house libraries where applicable (torpedo, cache_wrapper,
            mongoose, tortoise_wrapper, openapi for Python code).
            - Class and function reusability: Identify opportunities to reuse existing classes and functions.
            </reusability_guidelines>
            
            3. Maintainability:
            <maintainability_guidelines>
            - Refactoring: Suggest refactoring to improve code maintainability.
            - Technical Debt: Identify areas where technical debt needs to be addressed.
            - Deep Nesting: Flag instances of deep nesting and overly complex functions.
            - Commented Code: Ensure there is no commented-out code.
            </maintainability_guidelines>
            
            4. Code Robustness:
            <code_robustness_guidelines>
            - Exception Handling: Examine exception handling in log messages, avoiding generic exceptions.
            - API Errors: Ensure proper handling of downstream API errors.
            - Testing: Recommend writing unit tests for new features and bug fixes.
            - Fallback Mechanisms: Suggest implementing fallback mechanisms for critical operations.
            - Timeouts and Retries: Recommend setting reasonable timeouts and implementing retry logic.
            </code_robustness_guidelines>
            
            5. Code Quality:
            <code_quality_guidelines>
            - Code Style: Check adherence to coding standards and style guides.
            - Best Practices: Suggest following coding best practices (DRY principle, avoiding magic numbers).
            - HTTP Methods: Ensure proper use of HTTP methods (GET, POST, UPDATE, PATCH).
            - Business Logic: Verify that no business logic is inside API controller methods.
            - Request/Response Validation: Check for proper validation of requests and responses.
            </<code_quality_guidelines>>
            
            6. Readability:
            <readability_guidelines>
            - Clarity: Assess the overall clarity and readability of the code.
            - Complexity: Identify areas of high complexity and suggest simplifications.
            - Naming Conventions: Evaluate the use of clear and descriptive names for variables, functions, and
            classes.
            - Type Hints: Ensure functions have type hints for input and return types.
            </readability_guidelines>
            
            Analyze the code thoroughly and provide your feedback in the following XML format:
            
            {self.get_xml_review_comments_format(self.params['BUCKET'], self.params['AGENT_NAME'], self.agent_focus_area)} 

            If you are not able to comment due to any reason, be it an error, or you think the PR is good just give the review and root comments tag and don't put anything in it.
            Example:
            <review><comments></comments></review>
            
            Important instructions:
            1. Create exactly one <comment> block for each code maintainability issue found.
            2. Only comment on aspects related to the six categories mentioned above.
            3. Do not provide appreciation comments or positive feedback.
            4. Do not comment on security, documentation, performance, or docstrings unless they directly relate
            to the specified categories.
            5. Ensure that each comment is relevant and actionable.
            6. Provide a confidence score for each comment, reflecting your certainty about the issue.
            7. Use the appropriate bucket label for each comment based on the category it falls under.
            8. Do not repeat similar comments for multiple instances of the same issue.
            9. <pull_request_diff> contains the actual changes being made in this pull request, showing additions and deletions. 
                This is the primary focus for review comments. The diff shows:
                - Added lines (prefixed with +)
                - Removed lines (prefixed with -)
                - Context lines (no prefix)
                Only added lines and Removed lines changes should receive direct review comments.
            10. Comment ONLY on code present in <pull_request_diff> and Use <contextually_related_code_snippets> 
            only for understanding impact of change. 
            11. Do not comment on unchanged code unless directly impacted by the changes.
            12. Do not duplicate comments for similar issues across different locations.
            13. If you are suggesting any comment that is already catered please don't include those comment in response.
            14. Do not change the provided bucket name.
            15. Provide the exact, correct bucket name relevant to the issue. Ensure that the value is never left as a placeholder like "$BUCKET".
            
            Begin your review now, focusing on providing valuable feedback to improve the code quality and
            maintainability of the pull request.
        """

        if self.params.get("CUSTOM_PROMPT"):
            user_message = f"{user_message}\n{CUSTOM_PROMPT_INSTRUCTIONS}\n{self.params['CUSTOM_PROMPT']}"

        return UserAndSystemMessages(user_message=user_message, system_message=system_message)
