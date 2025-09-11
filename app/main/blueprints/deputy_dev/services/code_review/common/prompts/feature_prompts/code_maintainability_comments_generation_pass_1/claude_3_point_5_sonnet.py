from typing import Any, Dict

from deputydev_core.llm_handler.dataclasses.main import UserAndSystemMessages

from app.backend_common.dataclasses.dataclasses import PromptCategories
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

    def __init__(self, params: Dict[str, Any]) -> None:
        self.params = params
        self.agent_focus_area = AgentFocusArea.CODE_MAINTAINABILITY.value

    def get_system_prompt(self) -> str:
        return self.get_tools_specific_system_message(self.params)

    def get_prompt(self) -> UserAndSystemMessages:
        system_message = self.get_system_prompt()

        cached_message = self.get_user_cached_message_template(self.params)
        user_message = """
        
            You are specifically reviewing this pull request as a CODE QUALITY & MAINTAINABILITY ENGINEER.
            Your goal is to provide detailed, accurate feedback on code quality and maintainability aspects.
            
            Your expertise focuses on six critical areas:
            1. Architecture
            2. Reusability
            3. Maintainability
            4. Code Robustness
            5. Code Quality
            6. Readability

            - Review the code carefully, focusing on the following guidelines for each category:

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

            Important instructions:
            - Create exactly one <comment> block for each code maintainability issue found.
            - If you find something like certain change can have cascading effect in some other files too, Provide the exact file path, line number and the code snippet affected by the change.
            - Only comment on aspects related to the six categories mentioned above.
            - Do not provide appreciation comments or positive feedback.
            - Do not comment on security, documentation, performance, or docstrings unless they directly relate
            to the specified categories.
            - Ensure that each comment is relevant and actionable.
            - Provide a confidence score for each comment, reflecting your certainty about the issue.
            - Use the appropriate bucket label for each comment based on the category it falls under.
            - Do not repeat similar comments for multiple instances of the same issue.
            - <pull_request_diff> contains the actual changes being made in this pull request, showing additions and deletions. 
                This is the primary focus for review comments. The diff shows:
                - Added lines (prefixed with +)
                - Removed lines (prefixed with -)
                - Context lines (no prefix)
                Only added lines and Removed lines changes should receive direct review comments.
            - Comment ONLY on code present in <pull_request_diff> only for understanding impact of change not on unmodified lines. 
            - ** Do not comment on unchanged code unless directly impacted by the changes.**
            - Do not duplicate comments for similar issues across different locations.
            - If you are suggesting any comment that is already catered please don't include those comment in response.
            - Do not change the provided bucket name.
            - Provide the exact, correct bucket name relevant to the issue. Ensure that the value is never left as a placeholder like "$BUCKET".
            - Before suggesting a comment or corrective code verify diligently that the suggestion is not already incorporated in the <pull_request_diff>.

            Begin your review now, focusing on providing valuable feedback to improve the code quality and
            maintainability of the pull request.
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
