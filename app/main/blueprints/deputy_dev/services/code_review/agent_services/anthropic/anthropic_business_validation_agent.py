# flake8: noqa
from app.main.blueprints.deputy_dev.constants.constants import AgentTypes, TokenTypes
from app.main.blueprints.deputy_dev.services.code_review.agent_services.agent_base import (
    AgentServiceBase,
)
from app.main.blueprints.deputy_dev.services.code_review.context.context_service import (
    ContextService,
)
from app.main.blueprints.deputy_dev.services.setting_service import SettingService


class AnthropicBusinessValidationAgent(AgentServiceBase):
    def __init__(self, context_service: ContextService, is_reflection_enabled: bool):
        super().__init__(context_service, is_reflection_enabled, AgentTypes.BUSINESS_LOGIC_VALIDATION.value)
        self.agent_id = SettingService.pre_defined_agents_id(AgentTypes.BUSINESS_LOGIC_VALIDATION.value)

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
        - Focus solely on business logic correctness. Do not comment on other aspects such as security, code communication, performance, code maintainability, errors etc or provide
        appreciation for correct implementations..
        
        4. Prepare your review comments:
        - Only create a comment for unique, significant issues that directly impact business requirements.
        - Do not repeat similar comments for multiple instances of the same issue.
        - Do not provide general observations or suggestions unless they are critical to meeting the
        business requirements.
        
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
        - Provide clear and actionable feedback in your comments only for critical issues.
        - Use the confidence score to indicate how certain you are about each issue you raise.
        - Need not to do the appreciation comments for the things that are done correctly.
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
        
        <contextually_related_code_snippets>
        {$CONTEXTUALLY_RELATED_CODE_SNIPPETS}
        </contextually_related_code_snippets>
        
        <user_story>
        {$USER_STORY}
        </user_story>
    
        <product_research_document>
        {$PRODUCT_RESEARCH_DOCUMENT}
        </product_research_document>
        
        <junior_developer_comments>
        {$REVIEW_COMMENTS_BY_JUNIOR_DEVELOPER}
        </junior_developer_comments>
        
        </data>
        <guidelines>
        Your task is to review the changes made in the pull request and determine if they align with the
        given requirements. You should verify the accuracy, relevancy, and correctness of the junior
        developer's comments. You may add new comments, update existing ones, or remove unnecessary
        comments.
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
        8. Keep only comments that identify critical misalignments with business requirements.
        9. Remove any appreciation comments or general observations.
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
        
        Remember, your primary goal is to ensure that the changes in the pull request accurately implement
        the requirements specified in the user story and product research document. Do not get sidetracked
        by other aspects of code review that are not related to business logic correctness. 
        Note: Need not to do the appreciation comments for the things that are done correctly.
        </guidelines>
        
        Next, receive the comments from <thinking> and remove comments which follow below criteria mentioned 
        in new_guidelines
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
        <bucket>USER_STORY</bucket>
        </comment>
        <!-- Repeat the <comment> block for each issue that you find regarding business logic validation -->
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
            TokenTypes.PR_USER_STORY.value: self.context_service.pr_user_story_tokens,
            TokenTypes.PR_CONFLUENCE.value: self.context_service.confluence_doc_data_tokens,
        }

    async def should_execute(self):
        user_story = await self.context_service.get_user_story()
        if user_story:
            return True
