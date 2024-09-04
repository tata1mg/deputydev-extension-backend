# flake8: noqa
from app.main.blueprints.deputy_dev.constants.constants import AgentTypes, TokenTypes
from app.main.blueprints.deputy_dev.services.code_review.agent_services.agent_base import (
    AgentServiceBase,
)
from app.main.blueprints.deputy_dev.services.code_review.context.context_service import (
    ContextService,
)


class AnthropicCodeMaintainabilityAgent(AgentServiceBase):
    def __init__(self, context_service: ContextService, is_reflection_enabled: bool):
        super().__init__(context_service, is_reflection_enabled, AgentTypes.CODE_MAINTAINABILITY.value)

    def get_with_reflection_system_prompt_pass1(self):
        return """
        You are a senior developer tasked with reviewing a pull request for code quality and
        maintainability. Your goal is to provide detailed feedback on the following aspects:
        
        1. Architecture
        2. Reusability
        3. Maintainability
        4. Code Robustness
        5. Code Quality
        6. Readability
        """

    def get_with_reflection_user_prompt_pass1(self):
        return """
        Here is the information for the pull request you need to review:
        Pull Request Title:
        <pull_request_title>
        {$PULL_REQUEST_TITLE}
        </pull_request_title>
        
        Pull Request Description:
        <pull_request_description>
        {$PULL_REQUEST_DESCRIPTION}
        </pull_request_description>
        
        Pull Request Diff:
        <pull_request_diff>
        {$PULL_REQUEST_DIFF}
        </pull_request_diff>
        
        Contextually Related Code Snippets:
        <contextually_related_code_snippets>
        {$CONTEXTUALLY_RELATED_CODE_SNIPPETS}
        </contextually_related_code_snippets>
        
        Review the code carefully, focusing on the following guidelines for each category:
        
        1. Architecture:
        <architecture_guidelines>
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
        
        <review>
        <comments>
        <comment>
        <description>Describe the code maintainability issue and make sure to enclose description within <![CDATA[ ]]> to avoid XML parsing errors</description>
        <corrective_code>Rewrite or create new (in case of missing) code, docstring or documentation for
        developer to directly use it.
        Add this section under <![CDATA[ ]]> for avoiding xml paring error.
        Set this value empty string if there is no suggestive code.
        </corrective_code>
        <file_path>file path on which the comment is to be made</file_path>
        <line_number>line on which comment is relevant. get this value from `<>` block at each code start in
        input. Return the exact value present with label `+` or `-`</line_number>
        <confidence_score>floating point confidence score of the comment between 0.0 to 1.0  upto 2 decimal
        points</confidence_score>
        <bucket>{ARCHITECTURE | REUSABILITY | MAINTAINABILITY | CODE ROBUSTNESS | CODE QUALITY |
        READABILITY} - Either one of them depending on in which bucket the comment is falling.</bucket>
        </comment>
        <!-- Repeat the <comment> block for each code maintainability issue found -->
        </comments>
        </review>
        
        Important instructions:
        1. Create exactly one <comment> block for each code maintainability issue found.
        2. Only comment on aspects related to the six categories mentioned above.
        3. Do not comment on security, documentation, performance, or docstrings unless they directly relate
        to the specified categories.
        4. Ensure that each comment is relevant and actionable.
        5. Provide a confidence score for each comment, reflecting your certainty about the issue.
        6. Use the appropriate bucket label for each comment based on the category it falls under.
        
        Begin your review now, focusing on providing valuable feedback to improve the code quality and
        maintainability of the pull request.
        """

    def get_with_reflection_system_prompt_pass2(self):
        return """
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

    def get_with_reflection_user_prompt_pass2(self):
        return """
        First, examine the pull request information:

        <pull_request_title>
        {$PULL_REQUEST_TITLE}
        </pull_request_title>
        
        <pull_request_description>
        {$PULL_REQUEST_DESCRIPTION}
        </pull_request_description>
        
        <pull_request_diff>
        {$PULL_REQUEST_DIFF}
        </pull_request_diff>
        
        Here are the contextually relevant code snippets:
        
        <contextually_related_code_snippets>
        {$CONTEXTUALLY_RELATED_CODE_SNIPPETS}
        </contextually_related_code_snippets>
        
        Now, review the comments made by the junior developer:
        
        <junior_developer_comments>
        {$REVIEW_COMMENTS_BY_JUNIOR_DEVELOPER}
        </junior_developer_comments>
        
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
        
        Based on your analysis, create, modify, or remove comments as necessary. Output your review in the
        following XML format:
        
        <review>
        <comments>
        <comment>
        <description>Describe the code maintainability issue</description>
        <corrective_code>Rewrite or create new (in case of missing) code, docstring or documentation for
        developer to directly use it.
        Add this section under <![CDATA[ ]]> for avoiding xml paring error.
        Set this value empty string if there is no suggestive code.
        </corrective_code>
        <file_path>file path on which the comment is to be made</file_path>
        <line_number>line on which comment is relevant. get this value from `<>` block at each code start in
        input. Return the exact value present with label `+` or `-`</line_number>
        <confidence_score>floating point confidence score of the comment between 0.0 to 1.0  upto 2 decimal
        points</confidence_score>
        <bucket>{ARCHITECTURE | REUSABILITY | MAINTAINABILITY | CODE ROBUSTNESS | CODE QUALITY |
        READABILITY} - Either one of them depending on in which bucket the comment is falling.</bucket>
        </comment>
        <!-- Repeat the <comment> block for each code maintainability issue found -->
        </comments>
        </review>
        
        1. Ensure that each comment tag addresses a single issue. Provide a confidence
        score between 0.0 and 1.0 for each comment, reflecting your certainty in the observation. Categorize
        each comment into one of the six buckets: ARCHITECTURE, REUSABILITY, MAINTAINABILITY, CODE
        ROBUSTNESS, CODE QUALITY, or READABILITY.
        """

    def get_agent_specific_tokens_data(self):
        return {
            TokenTypes.PR_TITLE.value: self.context_service.pr_title_tokens,
            TokenTypes.PR_DESCRIPTION.value: self.context_service.pr_description_tokens,
            TokenTypes.PR_DIFF_TOKENS.value: self.context_service.pr_diff_tokens,
            TokenTypes.RELEVANT_CHUNK.value: self.context_service.embedding_input_tokens,
        }
