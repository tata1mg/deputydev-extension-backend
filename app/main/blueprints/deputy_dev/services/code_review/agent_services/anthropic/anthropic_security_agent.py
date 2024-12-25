# flake8: noqa
from app.main.blueprints.deputy_dev.constants.constants import AgentTypes, TokenTypes
from app.main.blueprints.deputy_dev.services.code_review.agent_services.agent_base import (
    AgentServiceBase,
)
from app.main.blueprints.deputy_dev.services.code_review.context.context_service import (
    ContextService,
)
from app.main.blueprints.deputy_dev.services.setting_service import SettingService


class AnthropicSecurityAgent(AgentServiceBase):
    def __init__(self, context_service: ContextService, is_reflection_enabled: bool):
        super().__init__(context_service, is_reflection_enabled, AgentTypes.SECURITY.value)
        self.agent_id = SettingService.pre_defined_agents_id(AgentTypes.SECURITY.value)

    def get_with_reflection_system_prompt_pass1(self):
        return """
        You are an Expert Application Security Engineer tasked with reviewing a pull request for security
        issues and vulnerabilities. Your goal is to thoroughly analyze the provided code diff and identify
        any potential security risks. 
        """

    def get_with_reflection_user_prompt_pass1(self):
        return """
        Follow these instructions carefully to conduct your review:

        1. Review the following information about the pull request:
        
        <pull_request_title>
        {$PULL_REQUEST_TITLE}
        </pull_request_title>
        
        <pull_request_description>
        {$PULL_REQUEST_DESCRIPTION}
        </pull_request_description>
        
        2. Carefully examine the code diff provided:
        
        <pull_request_diff>
        {$PULL_REQUEST_DIFF}
        </pull_request_diff>
        
        3. Conduct a comprehensive security review of the code changes, focusing on the following aspects:
        a. Input validation and sanitization
        b. Authentication and authorization
        c. Data encryption and protection
        d. Secure communication protocols
        e. Use of secure coding practices
        f. Third-party library usage and versioning
        g. Potential for injection attacks (SQL, XSS, CSRF, etc.)
        h. Secure configuration and environment variables
        i. Business logic flaws that could lead to security issues
        
        4. For each security issue or vulnerability you identify:
        a. Describe the issue, it's potential impact and its severity. This will be a comment on the PR.
        b. Corrected code - Rewrite the code snippet. How the code should be written ideally.
        c. File path - path of the file on which comment is being made
        d. line number - line on which comment is relevant. get this value from `<>` block at each code start in input. Return the exact value present with label `+` or `-`
        e. Confidence score - floating point confidence score of the comment between 0.0 to 1.0
        
        5. After completing your review, provide your findings in the following format:
        
        <review>
        <comments>
        <comment>
        <description>Describe the issue, it's potential impact and its severity (Critical, High, Medium, Low) and make sure to enclose description within <![CDATA[ ]]> to avoid XML parsing errors</description>
        <corrective_code>
        Rewrite the code snippet. How the code should be written ideally.
        Add this section under <![CDATA[ ]]> for avoiding xml paring error.
        Set this value empty string if there is no suggestive code.
        </corrective_code>
        <file_path>file path on which the comment is to be made</file_path>
        <line_number>line on which comment is relevant. get this value from `<>` block at each code start in input. Return the exact value present with label `+` or `-`</line_number>
        <confidence_score>floating point confidence score of the comment between 0.0 to 1.0  upto 2 decimal points</confidence_score>
        <bucket>SECURITY - Always this value since its a security agent</bucket>
        </comment>
        <!-- Repeat the <comment> block for each security issue found -->
        </comments>
        </review>
        
        8. Be thorough and err on the side of caution. It's better to flag a potential issue for further investigation than to miss a critical vulnerability.
        
        Keep in mind these important instructions when reviewing the code:
        -  Carefully analyze each change in the diff.
        -  Focus solely on security vulnerabilities as outlined above.
        -  Do not provide appreciation comments or positive feedback.
        -  Consider the context provided by contextually related code snippets.
        - For each finding or improvement, create a separate <comment> block within the <comments> section.
        -  If you find nothing to improve the PR, there should be no <comment> tags inside <comments> tag. Don't say anything other than identified issues/improvements. If no issue is identified, don't say anything.
        -  Ensure that your comments are clear, concise, and actionable.
        -  Provide specific line numbers and file paths for each finding.
        -  Assign appropriate confidence scores based on your certainty of the findings or improvements.
        -  Do not repeat similar comments for multiple instances of the same issue.
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
        """

    def get_with_reflection_system_prompt_pass2(self):
        return """You are a highly skilled code security expert tasked with reviewing a pull request for potential security
        issues and vulnerabilities. Your goal is to provide a thorough and accurate security review,
        improving upon an initial analysis. 
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
        
        <junior_developer_comments>
        {$REVIEW_COMMENTS_BY_JUNIOR_DEVELOPER}
        </junior_developer_comments>
        </data>
        
        <guidelines>
        Conduct a comprehensive security review of the code changes, focusing on the following aspects:
        a. Input validation and sanitization
        b. Authentication and authorization
        c. Data encryption and protection
        d. Secure communication protocols
        e. Use of secure coding practices
        f. Third-party library usage and versioning
        g. Potential for injection attacks (SQL, XSS, CSRF, etc.)
        h. Secure configuration and environment variables
        i. Business logic flaws that could lead to security issues
        
        4. For each security issue or vulnerability you identify:
        a. Describe the issue, it's potential impact and its severity. This will be a comment on the PR.
        b. Corrected code - Rewrite the code snippet. How the code should be written ideally.
        c. File path - path of the file on which comment is being made
        d. line number - line on which comment is relevant. get this value from `<>` block at each code start in input. Return the exact value present with label `+` or `-`
        e. Confidence score - floating point confidence score of the comment between 0.0 to 1.0
        
        Be thorough and err on the side of caution. It's better to flag a potential issue for further investigation than to miss a critical vulnerability.
        
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
        14.  If you are suggesting any comment that is already catered please don't include those comment in response.
        
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
        <description>Describe the issue, it's potential impact and its severity (Critical, High, Medium, Low) and make sure to enclose description within <![CDATA[ ]]> to avoid XML parsing errors</description>
        <corrective_code>
        Rewrite the code snippet. How the code should be written ideally.
        Add this section under <![CDATA[ ]]> for avoiding xml paring error.
        Set this value empty string if there is no suggestive code.
        </corrective_code>
        <file_path>file path on which the comment is to be made</file_path>
        <line_number>line on which comment is relevant. get this value from `<>` block at each code start in input. Return the exact value present with label `+` or `-`</line_number>
        <confidence_score>floating point confidence score of the comment between 0.0 to 1.0  upto 2 decimal points</confidence_score>
        <bucket>SECURITY - Always this value since its a security agent</bucket>
        </comment>
        <!-- Repeat the <comment> block for each security issue found -->
        </comments>
        </review>
        """

    def get_agent_specific_tokens_data(self):
        # TODO: PRDIFF update self.context_service.pr_diff_tokens to  self.context_service.pr_diff_tokens[agent_uuid]
        return {
            TokenTypes.PR_TITLE.value: self.context_service.pr_title_tokens,
            TokenTypes.PR_DESCRIPTION.value: self.context_service.pr_description_tokens,
            TokenTypes.PR_DIFF_TOKENS.value: self.context_service.pr_diff_tokens,
        }
