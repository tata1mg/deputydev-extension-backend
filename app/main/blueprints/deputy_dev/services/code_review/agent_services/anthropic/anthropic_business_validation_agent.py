# flake8: noqa
from app.main.blueprints.deputy_dev.constants.constants import AgentTypes, TokenTypes
from app.main.blueprints.deputy_dev.services.code_review.agent_services.agent_base import (
    AgentServiceBase,
)
from app.main.blueprints.deputy_dev.services.code_review.context.context_service import (
    ContextService,
)


class AnthropicBusinessValidationAgent(AgentServiceBase):
    def __init__(self, context_service: ContextService, is_reflection_enabled: bool):
        super().__init__(context_service, is_reflection_enabled, AgentTypes.BUSINESS_LOGIC_VALIDATION.value)

    def get_with_reflection_system_prompt_pass1(self):
        return """
        You are a senior developer tasked with reviewing a pull request for functional correctness. Your
        focus is on the business logic correctness of the PR against the given requirements.
        """

    def get_with_reflection_user_prompt_pass1(self):
        return """
        Follow these
        steps to complete your review:
        
        1. Review the pull request information:
        <pull_request_title>
        {$PULL_REQUEST_TITLE}
        </pull_request_title>
        
        <pull_request_description>
        {$PULL_REQUEST_DESCRIPTION}
        </pull_request_description>
        
        <pull_request_diff>
        {$PULL_REQUEST_DIFF}
        </pull_request_diff>
        
        <contextually_related_code_snippets>
        {$CONTEXTUALLY_RELATED_CODE_SNIPPETS}
        </contextually_related_code_snippets>
        
        2. Understand the requirements:
        <user_story>
        {$USER_STORY}
        </user_story>
        
        <product_research_document>
        {$PRODUCT_RESEARCH_DOCUMENT}
        </product_research_document>
        
        3. Analyze the changes:
        - Compare the changes in the pull request diff against the requirements in the user story and
        product research document.
        - Identify any discrepancies or misalignment's between the implemented changes and the stated
        requirements.
        - Focus solely on business logic correctness. Do not comment on other aspects such as security, code communication, performance, code maintainability, errors etc.
        
        4. Prepare your review comments:
        For each issue you identify, create a comment using the following format:
        
        <review>
        <comments>
        <comment>
        <description>Describe the issue and make sure to enclose description within <![CDATA[ ]]> to avoid XML parsing errors </description>
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
        <bucket>{USER_STORY} - Always this value since its a business logic validation agent</bucket>
        </comment>
        </comments>
        </review>
        
        Repeat the <comment> block for each issue you find regarding business logic validation.
        
        Remember:
        - Map exactly 1 comment to each comment tag in the output response.
        - Focus only on business logic correctness. Do not comment on any other aspects of code review.
        - Provide clear and actionable feedback in your comments.
        - Use the confidence score to indicate how certain you are about each issue you raise.
        - Need not to do the appreciation comments for the things that are done correctly.
        
        Your review should help ensure that the changes in the pull request accurately implement the
        requirements specified in the user story and product research document.
        """

    def get_with_reflection_system_prompt_pass2(self):
        return """
        You are a Principal Software Engineer tasked with reviewing a pull request for functional
        correctness, focusing specifically on business logic alignment with given requirements. You will be
        conducting a level 2 review, verifying and potentially modifying comments made by a junior
        developer.
        """

    def get_with_reflection_user_prompt_pass2(self):
        return """
        First, review the following pull request information:
        
        <pull_request_title>
        {$PULL_REQUEST_TITLE}
        </pull_request_title>
        
        <pull_request_description>
        {$PULL_REQUEST_DESCRIPTION}
        </pull_request_description>
        
        <pull_request_diff>
        {$PULL_REQUEST_DIFF}
        </pull_request_diff>
        
        <contextually_related_code_snippets>
        {$CONTEXTUALLY_RELATED_CODE_SNIPPETS}
        </contextually_related_code_snippets>
        
        Now, review the requirement information:
        
        <user_story>
        {$USER_STORY}
        </user_story>
        
        <product_research_document>
        {$PRODUCT_RESEARCH_DOCUMENT}
        </product_research_document>
        
        Your task is to review the changes made in the pull request and determine if they align with the
        given requirements. You should verify the accuracy, relevancy, and correctness of the junior
        developer's comments. You may add new comments, update existing ones, or remove unnecessary
        comments.
        
        Please provide your review in the following XML format:
        
        <review>
        <comments>
        <comment>
        <description>Describe the issue</description>
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
        <bucket>USER_STORY</bucket>
        </comment>
        <!-- Repeat the <comment> block for each issue that you find regarding business logic validation -->
        </comments>
        </review>
        
        When reviewing, please adhere to the following guidelines:
        1. Focus solely on business logic validation. Do not comment on other aspects such as security,
        documentation, performance, or docstrings.
        2. Ensure each comment is relevant to the changes made in the pull request and the given
        requirements.
        3. Provide clear and concise descriptions of any issues found.
        4. When suggesting corrective code, ensure it directly addresses the issue and can be easily
        implemented by the developer.
        5. Assign an appropriate confidence score to each comment based on your certainty of the issue.
        6. Use the exact line numbers from the diff when referencing specific lines of code.
        7. Always set the bucket value to "USER_STORY" as this is a business logic validation review.
        
        Remember, your primary goal is to ensure that the changes in the pull request accurately implement
        the requirements specified in the user story and product research document. Do not get sidetracked
        by other aspects of code review that are not related to business logic correctness. 
        Note: Need not to do the appreciation comments for the things that are done correctly.
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

    async def should_execute(self):
        user_story = await self.context_service.get_user_story()
        if user_story:
            return True
