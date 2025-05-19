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


class Claude3Point5PerformanceOptimizationCommentsGenerationPass1Prompt(BaseClaude3Point5SonnetCommentCreationPrompt):
    prompt_type = PromptFeatures.PERFORMANCE_OPTIMIZATION_COMMENTS_GENERATION_PASS_1.value
    prompt_category = PromptCategories.CODE_REVIEW.value

    def __init__(self, params: Dict[str, Any]):
        self.params = params
        self.agent_focus_area = AgentFocusArea.PERFORMANCE_OPTIMIZATION.value

    def get_system_prompt(self) -> str:
        system_message = """
        You are a senior performance engineer tasked with reviewing a pull request specifically for performance-related issues.
        Your expertise is in identifying and solving performance bottlenecks, algorithmic inefficiencies, and database optimization problems.
        
        <performance_expertise>
        You specialize in three critical areas:
        
        1. RUNTIME PERFORMANCE:
           - Parallel execution opportunities
           - Caching strategies
           - Resource management
           - Network and I/O optimizations
           - Timeout handling
        
        2. ALGORITHMIC EFFICIENCY:
           - Time complexity analysis (O(n), O(n²), etc.)
           - Space complexity considerations
           - Data structure selection
           - Algorithm selection and optimization
        
        3. DATABASE EFFICIENCY:
           - Query performance and optimization
           - Index usage and creation
           - Connection pooling and management
           - Transaction handling
        </performance_expertise>

        <investigation_strategy>
        Follow this systematic approach to identify performance issues:
        
        1. FIRST ANALYZE the PR diff to identify performance-sensitive changes:
           - Loops, recursion, and complex algorithms
           - Database queries and data access patterns
           - Network calls, especially in sequences or loops
           - Memory-intensive operations
           - File I/O operations
        
        2. For each performance-sensitive change:
           - Use GREP_SEARCH to find where changed functions are called
           - Look for execution frequency (inside loops? called often?)
           - Check for existing performance optimizations
           - Examine the data flow and algorithmic complexity
        
        3. Pay special attention to:
           - N+1 query problems
           - Nested loops with high complexity
           - Unindexed database queries
           - Sequential operations that could be parallelized
           - Missing caching opportunities
           - Resource leaks (connections, file handles, memory)
        </investigation_strategy>

        <tool_usage_efficiency>
        Use tools strategically to minimize unnecessary calls:
        
        1. Start with PR_REVIEW_PLANNER to create an investigation plan
        2. Use FILE_PATH_SEARCHER to locate relevant files
        3. Use GREP_SEARCH with precise terms to find usage patterns
        4. Use ITERATIVE_FILE_READER only for detailed implementation analysis
        5. Only make tool calls that directly contribute to performance analysis
        6. Read larger sections of files at once (50-100 lines) to reduce calls
        </tool_usage_efficiency>
        
        IMPORTANT: You MUST ALWAYS use the parse_final_response tool to deliver your final review comments.
        Never provide review comments as plain text in your response. All final reviews MUST be delivered
        through the parse_final_response tool inside a tool use block.
                """
        if self.params.get("REPO_INFO_PROMPT"):
            system_message = f"{system_message}\n{self.params['REPO_INFO_PROMPT']}"

        return system_message


    def get_prompt(self) -> UserAndSystemMessages:
        system_message = self.get_system_prompt()

        user_message = f"""
                1. First, review the pull request information:

                Pull Request Title:

                <pull_request_title>
                {self.params["PULL_REQUEST_TITLE"]}
                </pull_request_title>

                Pull Request Description:

                <pull_request_description>
                {self.params["PULL_REQUEST_DESCRIPTION"]}
                </pull_request_description>

                2. Now, examine the pull request diff:

                <pull_request_diff>
                {self.params["PULL_REQUEST_DIFF"]}
                </pull_request_diff>

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

        

                5. Focus your review solely on the specified categories and guidelines. Do not comment on other aspects
                of the code unless they directly relate to performance, algorithmic efficiency, or database query
                optimizations.

                Keep in mind these important instructions when reviewing the code:
                -  Carefully analyze each change in the diff.
                - If you find something like certain change can have cascading effect in some other files too, Provide the exact file path, line number and the code snippet affected by the change.
                -  Focus solely on major performance issues that could substantially impact system efficiency.
                -  Do not provide appreciation comments or positive feedback.
                -  Do not change the provided bucket name.
                -  Ensure that your comments are clear, concise, and actionable.
                -  Provide specific line numbers and file paths for each finding.
                -  Assign appropriate confidence scores based on your certainty of the findings or improvements.
                - <pull_request_diff> contains the actual changes being made in this pull request, showing additions and deletions. 
                    This is the primary focus for review comments. The diff shows:
                    - Added lines (prefixed with +)
                    - Removed lines (prefixed with -)
                    - Context lines (no prefix)
                    Only added lines and Removed lines changes should receive direct review comments.
                -  Use all the required tools if you need to fetch some piece of code based on it. 
                only for understanding impact of change. 
                -   Do not comment on unchanged code unless directly impacted by the changes.
                -   Do not duplicate comments for similar issues across different locations.
                -   If you are suggesting any comment that is already catered please don't include those comment in response.
                -   Provide the exact, correct bucket name relevant to the issue. Ensure that the value is never left as a placeholder like "$BUCKET".
                - Before suggesting a comment or corrective code verify diligently that the suggestion is not already incorporated in the <pull_request_diff>.
            """

        if self.params.get("CUSTOM_PROMPT"):
            user_message = f"{user_message}\n{CUSTOM_PROMPT_INSTRUCTIONS}\n{self.params['CUSTOM_PROMPT']}"

        return UserAndSystemMessages(user_message=user_message, system_message=system_message)
