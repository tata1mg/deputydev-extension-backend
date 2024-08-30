# flake8: noqa
from app.main.blueprints.deputy_dev.constants.constants import AgentTypes, TokenTypes
from app.main.blueprints.deputy_dev.services.code_review.agent_services.agent_base import (
    AgentServiceBase,
)
from app.main.blueprints.deputy_dev.services.code_review.context.context_service import (
    ContextService,
)


class AnthropicSecurityAgent(AgentServiceBase):
    def __init__(self, context_service: ContextService, is_reflection_enabled: bool):
        super().__init__(context_service, is_reflection_enabled, AgentTypes.SECURITY.value)

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
        <description>Describe the issue, it's potential impact and its severity (Critical, High, Medium, Low)</description>
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
        
        6. Remember to focus solely on security aspects of the code. Do not comment on code style,
        performance, or other non-security related issues unless they directly impact security.
        
        7. If you find no security issues, there should be no <comment> tags inside <comments> tag. Don't say anything other than identified issues. If no issue is identified, don't say anything.
        
        8. Be thorough and err on the side of caution. It's better to flag a potential issue for further investigation than to miss a critical vulnerability.
        """

    def get_with_reflection_system_prompt_pass2(self):
        return """You are a highly skilled code security expert tasked with reviewing a pull request for potential security
        issues and vulnerabilities. Your goal is to provide a thorough and accurate security review,
        improving upon an initial analysis. 
        """

    def get_with_reflection_user_prompt_pass2(self):
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
        <description>Describe the issue, it's potential impact and its severity (Critical, High, Medium, Low)</description>
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
        
        6. Remember to focus solely on security aspects of the code. Do not comment on code style,
        performance, or other non-security related issues unless they directly impact security.
        
        7. If you find no security issues, there should be no <comment> tags inside <comments> tag. Don't say anything other than identified issues. If no issue is identified, don't say anything.
        
        8. Be thorough and err on the side of caution. It's better to flag a potential issue for further investigation than to miss a critical vulnerability.
        """

    def get_agent_specific_tokens_data(self):
        return {
            TokenTypes.PR_TITLE.value: self.context_service.pr_title_tokens,
            TokenTypes.PR_DESCRIPTION.value: self.context_service.pr_description_tokens,
            TokenTypes.PR_DIFF_TOKENS.value: self.context_service.pr_diff_tokens,
        }
