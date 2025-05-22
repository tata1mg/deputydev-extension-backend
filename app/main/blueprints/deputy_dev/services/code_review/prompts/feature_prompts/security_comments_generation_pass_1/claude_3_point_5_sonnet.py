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


class Claude3Point5SecurityCommentsGenerationPass1Prompt(BaseClaude3Point5SonnetCommentCreationPrompt):
    prompt_type = PromptFeatures.SECURITY_COMMENTS_GENERATION_PASS_1.value
    prompt_category = PromptCategories.CODE_REVIEW.value

    def __init__(self, params: Dict[str, Any]):
        self.params = params
        self.agent_focus_area = AgentFocusArea.SECURITY.value

    def get_system_prompt(self) -> str:
        system_message = """
            You are an Expert Application Security Engineer tasked with reviewing a pull request for security
            issues and vulnerabilities. Your goal is to thoroughly analyze the provided code diff and identify
            any potential security risks.

            <security_review_approach>
            Unlike general code reviews, security reviews require a targeted approach:

            1. ANALYZE THE DIFF FIRST: Begin by thoroughly examining the PR diff for obvious security issues such as:
               - Hardcoded credentials
               - Insecure cryptographic implementations
               - Injection vulnerabilities in new/modified code
               - Authentication/authorization bypasses
               - And any other critical application security issues. 

            2. SELECTIVE TOOL USAGE: Only use tools when essential for security analysis, such as:
               - When you need to understand how user input flows through a system
               - When you need to verify if proper security controls exist in called methods
               - When you need to check if authentication/authorization is consistently applied
               - When tracing data flow for potential information leakage

            3. SECURITY-FOCUSED CONTEXT GATHERING: When you do use tools, focus queries specifically 
               on security-relevant information rather than general code understanding.
            </security_review_approach>

            IMPORTANT: 
            - You MUST ALWAYS use the parse_final_response tool to deliver your final review comments.
            Never provide review comments as plain text in your response. All final reviews MUST be delivered
            through the parse_final_response tool inside a tool use block.

        """
        if self.params.get("REPO_INFO_PROMPT"):
            system_message = f"{system_message}\n{self.params['REPO_INFO_PROMPT']}"

        return system_message

    def get_prompt(self) -> UserAndSystemMessages:
        system_message = self.get_system_prompt()

        user_message = f"""
            Follow these instructions carefully to conduct your review:

            1. Review the following information about the pull request:

            <pull_request_title>
            {self.params["PULL_REQUEST_TITLE"]}
            </pull_request_title>

            <pull_request_description>
            {self.params["PULL_REQUEST_DESCRIPTION"]}
            </pull_request_description>

                2. Carefully examine the code diff provided:

            <pull_request_diff>
            {self.params["PULL_REQUEST_DIFF"]}
            </pull_request_diff>

            4. For each security issue or vulnerability you identify:
                a. Describe the issue, it's potential impact and its severity. This will be a comment on the PR.
                b. Corrected code - Rewrite the code snippet. How the code should be written ideally.
                c. File path - path of the file on which comment is being made
                d. line number - line on which comment is relevant. get this value from `<>` block at each code start in input. Return the exact value present with label `+` or `-`
                e. Confidence score - floating point confidence score of the comment between 0.0 to 1.0

            5. Once you have gathered all necessary context and are confident in your findings, call the
                "parse_final_response" tool with your review comments:

            6. Be thorough and err on the side of caution. It's better to flag a potential issue for further investigation than to miss a critical vulnerability.
                
                <diff_first_security_analysis>
                - Begin with a thorough analysis of the PR diff BEFORE making any tool calls
                - Many common security vulnerabilities can be identified directly in the diff
                - Make tool calls ONLY when you need additional context that is essential for security assessment
                - For each potential security issue, consider if you truly need more context or if you can make a confident assessment from the diff
                </diff_first_security_analysis>

                Keep in mind these important instructions when reviewing the code:
                -  Carefully analyze each change in the diff.
                - If you find something like certain change can have cascading effect in some other files too, Provide the exact file path, line number and the code snippet affected by the change.
                -  Focus solely on security vulnerabilities as outlined above.
                -  Do not provide appreciation comments or positive feedback.
                -  Do not change the provided bucket name.
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
                -  Comment ONLY on code present in <pull_request_diff> 
                only for understanding impact of change. 
                -   Do not comment on unchanged code unless directly impacted by the changes.
                -   Do not duplicate comments for similar issues across different locations.
                -   If you are suggesting any comment that is already catered please don't include those comment in response.
                -   Provide the exact, correct bucket name relevant to the issue. Ensure that the value is never left as a placeholder like "$BUCKET".
                -   Use tools only when truly necessary for security assessment, not for general code understanding
                - Before suggesting a comment or corrective code verify diligently that the suggestion is not already incorporated in the <pull_request_diff>.
            """

        if self.params.get("CUSTOM_PROMPT"):
            user_message = f"{user_message}\n{CUSTOM_PROMPT_INSTRUCTIONS}\n{self.params['CUSTOM_PROMPT']}"

        return UserAndSystemMessages(user_message=user_message, system_message=system_message)
