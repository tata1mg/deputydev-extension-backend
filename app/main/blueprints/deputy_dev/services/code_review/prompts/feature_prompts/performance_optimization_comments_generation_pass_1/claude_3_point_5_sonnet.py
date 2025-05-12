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

    def get_prompt(self) -> UserAndSystemMessages:
        system_message = """
            You are a senior developer tasked with reviewing a pull request for code performance-related issues.
            Your focus should be on identifying issues in three main categories: Performance, Algorithmic
            efficiency, and Database query optimizations. Analyze the provided information and provide a
            detailed review based on the following guidelines.
        """
        if self.params.get("REPO_INFO_PROMPT"):
            system_message = f"{system_message}\n{self.params['REPO_INFO_PROMPT']}"

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
            
            3. Additionally, consider the contextually related code snippets:
            
            <contextually_related_code_snippets>
            {self.params["CONTEXTUALLY_RELATED_CODE_SNIPPETS"]}
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
            
            {self.get_xml_review_comments_format(self.params["BUCKET"], self.params["AGENT_NAME"], self.agent_focus_area)} 

            If you are not able to comment due to any reason, be it an error, or you think the PR is good just give the review and root comments tag and don't put anything in it.
            Example:
            <review><comments></comments></review>
            
            6. Focus your review solely on the specified categories and guidelines. Do not comment on other aspects
            of the code unless they directly relate to performance, algorithmic efficiency, or database query
            optimizations.
            
            Keep in mind these important instructions when reviewing the code:
            -  Carefully analyze each change in the diff.
            -  Focus solely on major performance issues that could substantially impact system efficiency.
            -  Do not provide appreciation comments or positive feedback.
            -  Do not change the provided bucket name.
            -  Consider the context provided by contextually related code snippets.
            -  For each finding or improvement, create a separate <comment> block within the <comments> section.
            -  If you find nothing to improve the PR, there should be no <comment> tags inside <comments> tag. Don't say anything other than identified issues/improvements. If no issue is identified, don't say anything.
            -  Ensure that your comments are clear, concise, and actionable.
            -  Provide specific line numbers and file paths for each finding.
            -  Assign appropriate confidence scores based on your certainty of the findings or improvements.
            - <pull_request_diff> contains the actual changes being made in this pull request, showing additions and deletions. 
                This is the primary focus for review comments. The diff shows:
                - Added lines (prefixed with +)
                - Removed lines (prefixed with -)
                - Context lines (no prefix)
                Only added lines and Removed lines changes should receive direct review comments.
            -  Comment ONLY on code present in <pull_request_diff> and Use <contextually_related_code_snippets> 
            only for understanding impact of change. 
            -   Do not comment on unchanged code unless directly impacted by the changes.
            -   Do not duplicate comments for similar issues across different locations.
            -   If you are suggesting any comment that is already catered please don't include those comment in response.
            -   Provide the exact, correct bucket name relevant to the issue. Ensure that the value is never left as a placeholder like "$BUCKET".
        """

        if self.params.get("CUSTOM_PROMPT"):
            user_message = f"{user_message}\n{CUSTOM_PROMPT_INSTRUCTIONS}\n{self.params['CUSTOM_PROMPT']}"

        return UserAndSystemMessages(user_message=user_message, system_message=system_message)
