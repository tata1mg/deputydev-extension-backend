# flake8: noqa
from app.main.blueprints.deputy_dev.constants.constants import AgentTypes, TokenTypes
from app.main.blueprints.deputy_dev.services.code_review.agent_services.agent_base import (
    AgentServiceBase,
)
from app.main.blueprints.deputy_dev.services.code_review.context.context_service import (
    ContextService,
)


class AnthropicCodeCommunicationAgent(AgentServiceBase):
    def __init__(self, context_service: ContextService, is_reflection_enabled: bool):
        super().__init__(context_service, is_reflection_enabled, AgentTypes.CODE_COMMUNICATION.value)

    def get_with_reflection_system_prompt_pass1(self):
        return """
        You are a code reviewer tasked with evaluating a pull request specifically for code communication
        aspects. Your focus will be on documentation, docstrings, and logging. You will be provided with the
        pull request title, description, and the PR's diff (Output of `git diff` command)
        """

    def get_with_reflection_user_prompt_pass1(self):
        return """
        
        1. Here's the information for the pull request you need to review:
        
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
        
        2. Next, please review the pull request focusing on the following aspects. Consider each of them as a bucket:
        
        <documentation_guidelines>
        - Evaluate the quality and presence of inline comments and annotations in the code.
        - Check for API documentation, including function descriptions and usage examples.
        - Assess the quality and completeness of project documentation such as README files and user guides.
        </documentation_guidelines>
        
        <docstrings_guidelines>
        - Verify that proper docstrings are present for each newly added function.
        - Check if class docstrings are missing.
        - Ensure that module docstrings are present.
        </docstrings_guidelines>
        
        <logging_guidelines>
        - Review the use of log levels (e.g., info, warn, error) in log messages.
        - Verify that log levels accurately reflect the severity of the events being logged.
        - Check for generic logging and examine if the log messages include sufficient information for
        understanding the context of the logged events.
        </logging_guidelines>
        
        3. For each bucket (Documentation, Docstrings, and Logging), provide your comments to be made on PR for improvements.
        Use the following format for your review comments:
        
        <review>
        <comments>
        <comment>
        <description>Describe the code communication issue and make sure to enclose description within <![CDATA[ ]]> to avoid XML parsing errors</description>
        <corrective_code>Rewrite or create new (in case of missing) code, docstring or documentation for developer
         to directly use it.
         Add this section under <![CDATA[ ]]> for avoiding xml paring error.
         Set this value empty string if there is no suggestive code.
        </corrective_code>
        <file_path>file path on which the comment is to be made</file_path>
        <line_number>line on which comment is relevant. get this value from `<>` block at each code start in input. Return the exact value present with label `+` or `-`</line_number>
        <confidence_score>floating point confidence score of the comment between 0.0 to 1.0  upto 2 decimal points</confidence_score>
        <bucket>{DOCUMENTATION | DOCSTRING | LOGGING} - Either one of them depending on in which bucket the comment is falling.</bucket>
        </comment>
        <!-- Repeat the <comment> block for each code communication issue found -->
        </comments>
        </review>
        
        4. Remember to focus solely on code communication aspects as outlined above. Do not comment on code
        functionality, performance, or other aspects outside the scope of documentation, docstrings, and
        logging.
        
        Keep in mind these important instructions when reviewing the code:
        1. Focus solely on major code communication issues as outlined above.
        2. Carefully analyze each change in the diff.
        3. For each finding or improvement, create a separate <comment> block within the <comments> section.
        4. If you find nothing to improve the PR, there should be no <comment> tags inside <comments> tag. Don't say anything other than identified issues/improvements. If no issue is identified, don't say anything.
        5. Ensure that your comments are clear, concise, and actionable.
        6. Provide specific line numbers and file paths for each finding.
        7. Assign appropriate confidence scores based on your certainty of the findings or suggestion
        8. Do not provide appreciation comments or positive feedback.
        9. Do not repeat similar comments for multiple instances of the same issue
        """

    def get_with_reflection_system_prompt_pass2(self):
        return """
        You are a senior developer expert at reviewing code for code communication aspects. Your task is to
        perform a level 2 review of a junior developer's comments on a pull request, focusing on
        documentation, docstrings, and logging.
        """

    def get_with_reflection_user_prompt_pass2(self):
        return """
        1. First, examine the pull request information:

        <pull_request_title>
        {$PULL_REQUEST_TITLE}
        </pull_request_title>
        
        <pull_request_description>
        {$PULL_REQUEST_DESCRIPTION}
        </pull_request_description>
        
        Now, review the diff of the pull request:
        
        <pull_request_diff>
        {$PULL_REQUEST_DIFF}
        </pull_request_diff>
        
        2. Next, carefully read the junior developer's review comments:
        
        <junior_developer_comments>
        {$REVIEW_COMMENTS_BY_JUNIOR_DEVELOPER}
        </junior_developer_comments>
        
        3. Your task is to review these comments for accuracy, relevancy, and correctness, considering the
        following criteria:
        
        <documentation_guidelines>
        - Quality and presence of inline comments and annotations
        - API documentation, including function descriptions and usage examples
        - Quality and completeness of project documentation (README files, user guides)
        </documentation_guidelines>
        
        <docstrings_guidelines>
        - Presence of proper docstrings for newly added functions
        - Presence of class docstrings
        - Presence of module docstrings
        </docstrings_guidelines>
        
        <logging_guidelines>
        - Appropriate use of log levels (info, warn, error)
        - Avoidance of generic logging
        - Inclusion of sufficient context in log messages
        </logging_guidelines>
        
        4. Review each comment made by the junior developer. You may:
        - Confirm and keep accurate comments
        - Modify comments that are partially correct or need improvement
        - Remove irrelevant or incorrect comments
        - Add new comments for issues the junior developer missed
        
        5. For each comment (kept, modified, or new), provide the following information in XML format:
        
        a. A clear description of the code communication issue
        b. Corrective code, docstring, or documentation that the developer can directly use
        c. The file path where the comment is relevant
        d. The line number where the comment is applicable (use the exact value with label '+' or '-' from
        the diff)
        e. A confidence score between 0.0 and 1.0
        f. The appropriate bucket (DOCUMENTATION, DOCSTRING, or LOGGING)
        
        6. Use the following XML format for your review comments:
        
        <review>
        <comments>
        <comment>
        <description>Describe the code communication issue</description>
        <corrective_code>
        Rewrite or create new (in case of missing) code, docstring or documentation for developer to directly use it.
        Add this section under <![CDATA[ ]]> for avoiding xml paring error.
        Set this value empty string if there is no suggestive code.
        </corrective_code>
        <file_path>file path on which the comment is to be made</file_path>
        <line_number>line on which comment is relevant. get this value from `<>` block at each code start in input. Return the exact value present with label `+` or `-`</line_number>
        <confidence_score>floating point confidence score of the comment between 0.0 to 1.0  upto 2 decimal points</confidence_score>
        <bucket>{DOCUMENTATION | DOCSTRING | LOGGING} - Either one of them depending on in which bucket the comment is falling.</bucket>
        </comment>
        <!-- Repeat the <comment> block for each code communication issue found -->
        </comments>
        </review>
        
        7. Remember to focus solely on code communication aspects as outlined above. Do not comment on code
        functionality, performance, or other aspects outside the scope of documentation, docstrings, and
        logging.
        
        Keep in mind these important instructions when reviewing the code:
        1. Carefully analyze each change in the diff.
        2. For each finding or improvement, create a separate <comment> block within the <comments> section.
        3. If you find nothing to improve the PR, there should be no <comment> tags inside <comments> tag. Don't say anything other than identified issues/improvements. If no issue is identified, don't say anything.
        5. Ensure that your comments are clear, concise, and actionable.
        6. Provide specific line numbers and file paths for each finding.
        7. Assign appropriate confidence scores based on your certainty of the findings or suggestion
        8. Do not include appreciation comments, minor suggestions, or repeated issues.
        """

    def get_agent_specific_tokens_data(self):
        return {
            TokenTypes.PR_TITLE.value: self.context_service.pr_title_tokens,
            TokenTypes.PR_DESCRIPTION.value: self.context_service.pr_description_tokens,
            TokenTypes.PR_DIFF_TOKENS.value: self.context_service.pr_diff_tokens,
            TokenTypes.RELEVANT_CHUNK.value: self.context_service.embedding_input_tokens,
            TokenTypes.PR_USER_STORY.value: self.context_service.pr_user_story_tokens,
            TokenTypes.PR_CONFLUENCE.value: self.context_service.confluence_doc_data_tokens,
        }
