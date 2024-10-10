# flake8: noqa
from app.main.blueprints.deputy_dev.constants.constants import AgentTypes, TokenTypes
from app.main.blueprints.deputy_dev.services.code_review.agent_services.agent_base import (
    AgentServiceBase,
)
from app.main.blueprints.deputy_dev.services.code_review.context.context_service import (
    ContextService,
)


class AnthropicPerformanceOptimisationAgent(AgentServiceBase):
    def __init__(self, context_service: ContextService, is_reflection_enabled: bool):
        super().__init__(context_service, is_reflection_enabled, AgentTypes.PERFORMANCE_OPTIMISATION.value)

    def get_with_reflection_system_prompt_pass1(self):
        return """
        You are a senior developer tasked with reviewing a pull request for code performance-related issues.
        Your focus should be on identifying issues in three main categories: Performance, Algorithmic
        efficiency, and Database query optimizations. Analyze the provided information and provide a
        detailed review based on the following guidelines.
        """

    def get_with_reflection_user_prompt_pass1(self):
        return """
        1. First, review the pull request information:
        
        Pull Request Title:
        
        <pull_request_title>
        {$PULL_REQUEST_TITLE}
        </pull_request_title>
        
        Pull Request Description:
        
        <pull_request_description>
        {$PULL_REQUEST_DESCRIPTION}
        </pull_request_description>
        
        2. Now, examine the pull request diff:
        
        <pull_request_diff>
        {$PULL_REQUEST_DIFF}
        </pull_request_diff>
        
        3. Additionally, consider the contextually related code snippets:
        
        <contextually_related_code_snippets>
        {$CONTEXTUALLY_RELATED_CODE_SNIPPETS}
        </contextually_related_code_snippets>
        
        4. Analyze the code for issues in the following categories:
        
        <performance_issues_guidelines>:
        - Parallel calls: Identify opportunities to execute multiple tasks in parallel if they are not
        dependent on each other.
        - Caching: Check if the code caches frequently accessed information, especially when retrieving data
        from downstream service APIs or databases.
        - Timeout: Ensure proper timeouts are added for API calls or any other network calls.
        - General optimizations - General code optimizations best practices.
        - Critical resource leaks or memory management issues
        </performance_issues_guidelines>
        
        <algorithmic_efficiency_guidelines>
        - Time Complexity: Evaluate the time complexity of algorithms and suggest optimizations.
        - Space Complexity: Assess the space complexity and recommend ways to reduce memory usage.
        - Data Structures: Suggest more efficient data structures to improve performance.
        </algorithmic_efficiency_guidelines>
        
        <database_query_optimisation_guidelines>
        - Query Optimization: Review the efficiency of database queries and suggest optimizations (e.g.,
        indexing, query refactoring).
        - Connection Management: Evaluate database connection handling and pooling strategies.
        </database_query_optimisation_guidelines>
        
        5. For each category, provide your analysis in the following format:
        
        <review>
        <comments>
        <comment>
        <description>Describe the performance issue and make sure to enclose description within <![CDATA[ ]]> to avoid XML parsing errors</description>
        <corrective_code>
        Rewrite code snippet to remedy the issue.
        Add this section under <![CDATA[ ]]> for avoiding xml paring error.
        Set this value empty string if there is no suggestive code.
        </corrective_code>
        <file_path>file path on which the comment is to be made</file_path>
        <line_number>line on which comment is relevant. get this value from `<>` block at each code start in input. Return the exact value present with label `+` or `-`</line_number>
        <confidence_score>floating point confidence score of the comment between 0.0 to 1.0 upto 2 decimal points</confidence_score>
        <bucket>{PERFORMANCE | ALGORITHM_EFFICIENCY | DATABASE_PERFORMANCE} - Either one of them depending on in which bucket the comment is falling.</bucket>
        </comment>
        <!-- Repeat the <comment> block for each code communication issue found -->
        </comments>
        </review>
        
        6. Focus your review solely on the specified categories and guidelines. Do not comment on other aspects
        of the code unless they directly relate to performance, algorithmic efficiency, or database query
        optimizations.
        
        Keep in mind these important instructions when reviewing the code:
        1. Carefully analyze each change in the diff.
        2. Focus solely on major performance issues that could substantially impact system efficiency.
        3. Do not provide appreciation comments or positive feedback.
        4. Consider the context provided by contextually related code snippets.
        5. For each finding or improvement, create a separate <comment> block within the <comments> section.
        6. If you find nothing to improve the PR, there should be no <comment> tags inside <comments> tag. Don't say anything other than identified issues/improvements. If no issue is identified, don't say anything.
        7. Ensure that your comments are clear, concise, and actionable.
        8. Provide specific line numbers and file paths for each finding.
        9. Assign appropriate confidence scores based on your certainty of the findings or improvements.
        10. Do not repeat similar comments for multiple instances of the same issue.
        
        """

    def get_with_reflection_system_prompt_pass2(self):
        return """
        You are a Principal Software Engineer expert at reviewing pull requests for code performance related
        issues. Your task is to perform a level 2 review of a junior developer's comments on a pull request,
        focusing on performance, algorithmic efficiency, and database query optimizations.
        """

    def get_with_reflection_user_prompt_pass2(self):
        return """
        1. First, examine the pull request information:

        Pull Request Title:
        
        <pull_request_title>
        {$PULL_REQUEST_TITLE}
        </pull_request_title>
        
        Pull Request Description:
        
        <pull_request_description>
        {$PULL_REQUEST_DESCRIPTION}
        </pull_request_description>
        
        <pull_request_diff>
        {$PULL_REQUEST_DIFF}
        </pull_request_diff>
        
        2. Also have a look at contextually related code snippets:
        
        <contextually_related_code_snippets>
        {$CONTEXTUALLY_RELATED_CODE_SNIPPETS}
        </contextually_related_code_snippets>
        
        
        3. Now, review the comments made by the junior developer:
        
        <junior_developer_comments>
        {$JUNIOR_DEVELOPER_COMMENTS}
        </junior_developer_comments>
        
        4. Your task is to review these comments for accuracy, relevancy, and correctness. Consider the
        following guidelines while reviewing:
        
        <performance>
        - Parallel calls: Suggest executing multiple tasks parallelly if they are not dependent.
        - Caching: Ensure code caches frequently accessed information from downstream service APIs or
        databases.
        - Timeout: Verify proper timeouts are added for API calls or any other network calls.
        </performance>
        
        <algorithmic_efficiency>
        - Time Complexity: Evaluate the time complexity of algorithms and suggest optimizations.
        - Space Complexity: Assess space complexity and recommend ways to reduce memory usage.
        - Data Structures: Suggest more efficient data structures to improve performance.
        </algorithmic_efficiency>
        
        
        <database_query_optimization>
        - Query Optimization: Evaluate the efficiency of database queries and suggest optimizations (e.g.,
        indexing, query refactoring).
        - Connection Management: Review database connection handling and pooling strategies.
        <database_query_optimization>
        
        5. You are free to add more comments, update existing comments, or delete unnecessary comments.  For each category, provide your analysis in the following format:
        
        <review>
        <comments>
        <comment>
        <description>Describe the performance issue</description>
        <corrective_code>
        Rewrite code snippet to remedy the issue.
        Add this section under <![CDATA[ ]]> for avoiding xml paring error.
        Set this value empty string if there is no suggestive code.
        </corrective_code>
        <file_path>file path on which the comment is to be made</file_path>
        <line_number>line on which comment is relevant. get this value from `<>` block at each code start in input. Return the exact value present with label `+` or `-`</line_number>
        <confidence_score>floating point confidence score of the comment between 0.0 to 1.0 upto 2 decimal points</confidence_score>
        <bucket>{PERFORMANCE | ALGORITHM_EFFICIENCY | DATABASE_PERFORMANCE} - Either one of them depending on in which bucket the comment is falling.</bucket>
        </comment>
        <!-- Repeat the <comment> block for each code communication issue found -->
        </comments>
        </review>
        
        Keep in mind these important instructions when reviewing the code:
        1. Carefully analyze each change in the diff.
        2. Focus solely on major performance issues that could substantially impact system efficiency.
        3. Do not include appreciation comments, minor suggestions, or repeated issues.
        4. Consider the context provided by contextually related code snippets.
        5. For each finding or improvement, create a separate <comment> block within the <comments> section.
        6. If you find nothing to improve the PR, there should be no <comment> tags inside <comments> tag. Don't say anything other than identified issues/improvements. If no issue is identified, don't say anything.
        7. Ensure that your comments are clear, concise, and actionable.
        8. Provide specific line numbers and file paths for each finding.
        9. Assign appropriate confidence scores based on your certainty of the findings or improvements.
        """

    def get_agent_specific_tokens_data(self):
        return {
            TokenTypes.PR_TITLE.value: self.context_service.pr_title_tokens,
            TokenTypes.PR_DESCRIPTION.value: self.context_service.pr_description_tokens,
            TokenTypes.PR_DIFF_TOKENS.value: self.context_service.pr_diff_tokens,
            TokenTypes.RELEVANT_CHUNK.value: self.context_service.embedding_input_tokens,
        }
