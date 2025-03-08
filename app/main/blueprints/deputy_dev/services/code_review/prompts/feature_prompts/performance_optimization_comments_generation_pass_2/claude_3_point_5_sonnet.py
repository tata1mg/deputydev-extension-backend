from typing import Any, Dict

from app.backend_common.services.llm.dataclasses.main import UserAndSystemMessages
from app.main.blueprints.deputy_dev.constants.constants import (
    CUSTOM_PROMPT_INSTRUCTIONS,
)

from ...base_prompts.claude_3_point_5_sonnet_comment_creation import (
    BaseClaude3Point5SonnetCommentCreationPrompt,
)
from ...dataclasses.main import PromptFeatures


class Claude3Point5PerformanceOptimizationCommentsGenerationPass2Prompt(BaseClaude3Point5SonnetCommentCreationPrompt):
    prompt_type = PromptFeatures.PERFORMANCE_OPTIMIZATION_COMMENTS_GENERATION_PASS_2.value

    def __init__(self, params: Dict[str, Any]):
        self.params = params

    def get_prompt(self) -> UserAndSystemMessages:
        system_message = """
            You are a Principal Software Engineer expert at reviewing pull requests for code performance related
            issues. Your task is to perform a level 2 review of a junior developer's comments on a pull request,
            focusing on performance, algorithmic efficiency, and database query optimizations.
        """
        if self.params.get("REPO_INFO_PROMPT"):
            system_message = f"{system_message}\n{self.params['REPO_INFO_PROMPT']}"

        user_message = f"""
            First, review the pr for provided data and guidelines and keep your response in <thinking> tag.
            
            <data>
            Pull Request Title:
            
            <pull_request_title>
            {self.params['PULL_REQUEST_TITLE']}
            </pull_request_title>
            
            Pull Request Description:
            <pull_request_description>
            {self.params['PULL_REQUEST_DESCRIPTION']}
            </pull_request_description>
            
            <pull_request_diff>
            {self.params['PULL_REQUEST_DIFF']}
            </pull_request_diff>
            
            Here are the contextually relevant code snippets:
            <contextually_related_code_snippets>
            {self.params['CONTEXTUALLY_RELATED_CODE_SNIPPETS']}
            </contextually_related_code_snippets>
            
            <junior_developer_comments>
            {self.params['JUNIOR_DEVELOPER_COMMENTS']}
            </junior_developer_comments>
            </data>
            
            <guidelines>
            Your task is to review these comments for accuracy, relevancy, and correctness. Consider the
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
            14.  Before suggesting a comment or corrective code verify diligently that the suggestion is not already incorporated in the <pull_request_diff>.
            15.  Do not change the provided bucket name.
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
            <bucket>$BUCKET</bucket>
            </comment>
            <!-- Repeat the <comment> block for each code communication issue found -->
            </comments>
            </review>
        """

        if self.params.get("CUSTOM_PROMPT"):
            user_message = f"{user_message}\n{CUSTOM_PROMPT_INSTRUCTIONS}\n{self.params['CUSTOM_PROMPT']}"

        return UserAndSystemMessages(user_message=user_message, system_message=system_message)
