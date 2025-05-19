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


class Claude3Point5CodeCommunicationCommentsGenerationPass1Prompt(BaseClaude3Point5SonnetCommentCreationPrompt):
    prompt_type = PromptFeatures.CODE_COMMUNICATION_COMMENTS_GENERATION_PASS_1.value
    prompt_category = PromptCategories.CODE_REVIEW.value

    def __init__(self, params: Dict[str, Any]):
        self.params = params
        self.agent_focus_area = AgentFocusArea.CODE_COMMUNICATION.value

    def get_system_prompt(self) -> str:
        system_message = """
        You are a code reviewer tasked with evaluating a pull request specifically for code communication
        aspects. Your focus will be on documentation, docstrings, and logging. You will be provided with the
        pull request title, description, and the PR's diff (Output of `git diff` command)

        You must use the provided tools iteratively to fetch any code context needed that you need to review the pr. 
        Do not hallucinate code—always call a tool when you need to inspect definitions, functions, or file contents beyond the diff.

        <tool_usage_guidelines>
        Unlike other agents that need extensive context, your primary focus should be analyzing what's directly visible in the diff. Only use code search tools when absolutely necessary, following these principles:

        1. ANALYZE THE DIFF FIRST: Most documentation, docstring, and logging issues can be identified directly in the PR diff without additional context.

        2. MINIMIZE TOOL CALLS: Only call tools when you cannot make a confident assessment based on the diff alone, such as:
           - When you need to verify if documentation exists in parent classes
           - When you need to check consistency with existing documentation patterns
           - When you need to understand broader context that might affect logging requirements
           - Verify if you are not sure about imported elements are already present in the unchanged sections

        3. BATCH YOUR QUERIES: If you must use a tool, gather all similar questions and make a single comprehensive query rather than multiple small ones.
        4. No matter what If you provide final comments always call parse_final_response and provide comments in format provided in tool. 
        </tool_usage_guidelines>

        IMPORTANT: You MUST ALWAYS use the parse_final_response tool to deliver your final review comments.
        Never provide review comments as plain text in your response. All final reviews MUST be delivered
        through the parse_final_response tool inside a tool use block.

        <searching_and_reading>
        You have tools to search the codebase and read files. Follow these rules regarding tool calls:
        1. If available, heavily prefer the function, class search,  grep search, file search, and list dir tools.
        2. If you need to read a file, prefer to read larger sections of the file at once over multiple smaller calls.
        3. If you have found a reasonable code chunk you are confident with to provide a review comment, do not continue calling tools. Provide the review comment from the information you have found.
        </searching_and_reading>
        
    IMPORTANT: 
    - You MUST ALWAYS use the parse_final_response tool to deliver your final review comments.
    Never provide review comments as plain text in your response. All final reviews MUST be delivered
    through the parse_final_response tool inside a tool use block.
    - If any change has impacting change in other files, function, class where it was used. Provide the exact impacting areas in comment description.
    """

        if self.params.get("REPO_INFO_PROMPT"):
            system_message = f"{system_message}\n{self.params['REPO_INFO_PROMPT']}"

        return system_message


    def get_prompt(self) -> UserAndSystemMessages:
        system_message = self.get_system_prompt()

        user_message = f"""
            1. Here's the information for the pull request you need to review:
            
            Pull Request Title:
            <pull_request_title>
            {self.params["PULL_REQUEST_TITLE"]}
            </pull_request_title>
            
            Pull Request Description:
            <pull_request_description>
            {self.params["PULL_REQUEST_DESCRIPTION"]}
            </pull_request_description>
            
            Pull Request Diff:
            <pull_request_diff>
            {self.params["PULL_REQUEST_DIFF"]}
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

        
            3. Remember to focus solely on code communication aspects as outlined above. Do not comment on code
            functionality, performance, or other aspects outside the scope of documentation, docstrings, and
            logging.
            
            <diff_first_approach>
            - Begin by thoroughly analyzing only the PR diff without making any tool calls
            - Most documentation, docstring, and logging issues can be identified directly from the diff
            - Only after completing your diff analysis, determine if any tool calls are genuinely needed
            - Make tool calls only for specific uncertainties you cannot resolve from the diff alone
            </diff_first_approach>
            
            Keep in mind these important instructions when reviewing the code:
            - Focus solely on major code communication issues as outlined above.
            - If you find something like certain change can have cascading effect in some other files too, Provide the exact file path, line number and the code snippet affected by the change.
            - Carefully analyze each change in the diff.
            - Ensure that your comments are clear, concise, and actionable.
            - Provide specific line numbers and file paths for each finding.
            - Assign appropriate confidence scores based on your certainty of the findings or suggestion
            - Do not provide appreciation comments or positive feedback.
            - Do not change the provided bucket name.
            - <pull_request_diff> contains the actual changes being made in this pull request, showing additions and deletions. 
                This is the primary focus for review comments. The diff shows:
                - Added lines (prefixed with +)
                - Removed lines (prefixed with -)
                - Context lines (no prefix)
                Only added lines and Removed lines changes should receive direct review comments.
            -   Do not comment on unchanged code unless directly impacted by the changes.
            -   Do not duplicate comments for similar issues across different locations.
            -   If you are suggesting any comment that is already catered please don't include those comment in response.
            -   Provide the exact, correct bucket name relevant to the issue. Ensure that the value is never left as a placeholder like "$BUCKET".
            -  Use all the required tools if you need to fetch some piece of code based on it. 
            - Before suggesting a comment or corrective code verify diligently that the suggestion is not already incorporated in the <pull_request_diff>.
        """

        if self.params.get("CUSTOM_PROMPT"):
            user_message = f"{user_message}\n{CUSTOM_PROMPT_INSTRUCTIONS}\n{self.params['CUSTOM_PROMPT']}"

        return UserAndSystemMessages(user_message=user_message, system_message=system_message)
