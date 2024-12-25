# flake8: noqa
from app.main.blueprints.deputy_dev.constants.constants import AgentTypes, TokenTypes
from app.main.blueprints.deputy_dev.services.code_review.agent_services.agent_base import (
    AgentServiceBase,
)
from app.main.blueprints.deputy_dev.services.code_review.context.context_service import (
    ContextService,
)
from app.main.blueprints.deputy_dev.services.setting_service import SettingService


class AnthropicErrorAgent(AgentServiceBase):
    def __init__(self, context_service: ContextService, is_reflection_enabled: bool):
        super().__init__(context_service, is_reflection_enabled, AgentTypes.ERROR.value)
        self.agent_id = SettingService.pre_defined_agents_id(AgentTypes.ERROR.value)

    def get_with_reflection_system_prompt_pass1(self):
        return """
        You are a senior developer tasked with reviewing a pull request for errors. Your goal is to identify
        and comment on various types of errors in the code. Focus solely on finding and reporting errors,
        not on other aspects of code review.
        """

    def get_with_reflection_user_prompt_pass1(self):
        return """
        Here's the information about the pull request:
        
        <pull_request_title>
        {$PULL_REQUEST_TITLE}
        </pull_request_title>
        
        <pull_request_description>
        {$PULL_REQUEST_DESCRIPTION}
        </pull_request_description>
        
        Now, examine the following diff and related code snippets:
        
        <pull_request_diff>
        {$PULL_REQUEST_DIFF}
        </pull_request_diff>
        
        <contextually_related_code_snippets>
        {$CONTEXTUALLY_RELATED_CODE_SNIPPETS}
        </contextually_related_code_snippets>
        
        Focus on identifying the following types of errors:
        
        1. Runtime errors
        2. Syntax errors
        3. Logical errors
        4. Semantic errors
        5. Edge cases
        6. Unhandled exceptions
        
        Guidelines for identifying each error type:
        1. Runtime Errors:
        <runtime_error_guidelines>
        - Potential issues that could cause the program to crash or behave unexpectedly
        during execution.
        </runtime_error_guidelines>
        
        2. Syntax Errors:
        <syntax_error_guidelines>
        - Check for missing semicolons, mismatched parentheses, or incorrect keyword usage.
        </syntax_error_guidelines>
        
        3. Logical Errors:
        <logical_error_guidelines>
        - Analyze the code's flow and algorithms for incorrect calculations or faulty
        conditionals.
        </logical_error_guidelines>
        
        4. Semantic Errors:
        <semantic_error_guidelines>
        - Identify misuse of language features, such as improper type conversions or
        incorrect method calls.
        </semantic_error_guidelines>
        
        5. Edge Cases:
        <edge_cases_guidelines>
        - Consider extreme or unusual inputs that might cause unexpected behavior.
        </edge_cases_guidelines>
        
       6. Unhandled exceptions:
        <unhandled_exceptions>
        - Check for Unhandled exceptions in critical code paths.
        </unhandled_exceptions> 
        
        Analyze the code thoroughly and provide your feedback in the following XML format:
        
        <review>
        <comments>
        <comment>
        <description>Describe the error and its potential impact and make sure to enclose description within <![CDATA[ ]]> to avoid XML parsing errors</description>
        <corrective_code>
        Provide corrected code or suggest improvements.
        Add this section under <![CDATA[ ]]> for avoiding xml paring error.
        Set this value empty string if there is no suggestive code.
        </corrective_code>
        <file_path>Specify the file path where the error occurs</file_path>
        <line_number>Indicate the line number (use the exact value with '+' or '-' from the
        diff)</line_number>
        <confidence_score>Assign a confidence score between 0.0 and 1.0 (up to 2 decimal
        points)</confidence_score>
        <bucket>{ERROR}</bucket>
        </comment>
        <!-- Repeat the <comment> block for each error found -->
        </comments>
        </review>
        
        Important: Focus exclusively on identifying and reporting errors. Do not comment on other aspects of
        code review such as security, documentation, performance, or docstrings unless they directly relate
        to an error.
        
        When reviewing the code:
        -  Carefully analyze each change in the diff.
        -  Focus solely on major error-related issues as outlined above.
        -  Do not comment on minor issues or hypothetical edge cases
        -  Do not provide appreciation comments or positive feedback.
        -  Consider the context provided by related code snippets.
        -  For each error found, create a separate <comment> block within the <comments> section.
        -  Ensure that your comments are clear, concise, and actionable.
        -  Provide specific line numbers and file paths for each error.
        -  Assign appropriate confidence scores based on your certainty of the error.
        - Do not repeat similar comments for multiple instances of the same issue.
        - <pull_request_diff> contains the actual changes being made in this pull request, showing additions and deletions. 
            This is the primary focus for review comments. The diff shows:
            - Added lines (prefixed with +)
            - Removed lines (prefixed with -)
            - Context lines (no prefix)
            Only  Added lines and Removed lines  changes should receive direct review comments.
        -  Comment ONLY on code present in <pull_request_diff> and Use <contextually_related_code_snippets> 
        only for understanding impact of change. 
        -   Do not comment on unchanged code unless directly impacted by the changes.
        -   Do not duplicate comments for similar issues across different locations.
        -   If you are suggesting any comment that is already catered please don't include those comment in response.
        
        Remember to maintain a professional and constructive tone in your comments. Your goal is to help
        improve the code quality by identifying and explaining errors accurately.
        """

    def get_with_reflection_system_prompt_pass2(self):
        return """
        You are a Principal Software Engineer expert at reviewing pull requests for errors. Your task is to
        review the comments made by a junior developer on a pull request, verifying their accuracy,
        relevancy, and correctness. You will then provide your own assessment, which may include adding more
        comments, updating existing ones, or deleting unnecessary ones.
        """

    def get_with_reflection_user_prompt_pass2(self):
        return """
        First, review the pr for provided data and guidelines and keep your response in <thinking> tag.
        <data>
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
        <contextual_code_snippets>
        {$CONTEXTUALLY_RELATED_CODE_SNIPPETS}
        </contextual_code_snippets>
        
        Here are the review comments made by the junior developer:
        <junior_developer_comments>
        {$REVIEW_COMMENTS_BY_JUNIOR_DEVELOPER}
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
        12.  If you are suggesting any comment that is already catered please don't include those comment in response.
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
        <description>Describe the error and its potential impact and make sure to enclose description within <![CDATA[ ]]> to avoid XML parsing errors</description>
        <corrective_code>
        Provide corrected code or suggest improvements.
        Add this section under <![CDATA[ ]]> for avoiding xml paring error.
        Set this value empty string if there is no suggestive code.
        </corrective_code>
        <file_path>Specify the file path where the error occurs</file_path>
        <line_number>Indicate the line number (use the exact value with '+' or '-' from the
        diff)</line_number>
        <confidence_score>Assign a confidence score between 0.0 and 1.0 (up to 2 decimal
        points)</confidence_score>
        <bucket>{ERROR}</bucket>
        </comment>
        <!-- Repeat the <comment> block for each error found -->
        </comments>
        </review>
        """

    def get_agent_specific_tokens_data(self):
        # TODO: PRDIFF update self.context_service.pr_diff_tokens to  self.context_service.pr_diff_tokens[agent_uuid]
        return {
            TokenTypes.PR_TITLE.value: self.context_service.pr_title_tokens,
            TokenTypes.PR_DESCRIPTION.value: self.context_service.pr_description_tokens,
            TokenTypes.PR_DIFF_TOKENS.value: self.context_service.pr_diff_tokens,
            TokenTypes.RELEVANT_CHUNK.value: self.context_service.embedding_input_tokens,
        }
