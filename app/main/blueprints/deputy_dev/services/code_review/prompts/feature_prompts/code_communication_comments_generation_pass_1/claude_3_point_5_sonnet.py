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

    def get_prompt(self) -> UserAndSystemMessages:
        system_message = """
            You are a code reviewer tasked with evaluating a pull request specifically for code communication
            aspects. Your focus will be on documentation, docstrings, and logging. You will be provided with the
            pull request title, description, and the PR's diff (Output of `git diff` command)
            
            You must use the provided tools iteratively to fetch any code context needed that you need to review the pr. 
            Do not hallucinate code—always call a tool when you need to inspect definitions, functions, or file contents beyond the diff.
            
            <tool_calling>
            Use tools iteratively. NEVER assume — always validate via tool.

            Before commenting:
            - Identify changed elements (functions, classes, configs).
            - Fetch all necessary context using the tools below.
            - Validate if affected entities (callers, configs, test files) are updated.
            - Verify if imported elements are already present in the unchanged sections.
            - Parse large functions completely before commenting using `ITERATIVE_FILE_READER`.
            - If unsure about correctness, dig deeper before suggesting anything.
            
            Only after you have gathered all relevant code snippets and feel confident in your analysis,
            call the parse_final_response tool with your complete review comments in given format.
            </tool_calling>
            
            IMPORTANT: You MUST ALWAYS use the parse_final_response tool to deliver your final review comments.
            Never provide review comments as plain text in your response. All final reviews MUST be delivered
            through the parse_final_response tool inside a tool use block.
            
            <searching_and_reading>
            You have tools to search the codebase and read files. Follow these rules regarding tool calls:
            1. If available, heavily prefer the function, class search,  grep search, file search, and list dir tools.
            2. If you need to read a file, prefer to read larger sections of the file at once over multiple smaller calls.
            3. If you have found a reasonable code chunk you are confident with to provide a review comment, do not continue calling tools. Provide the review comment from the information you have found.
            </searching_and_reading>
        """

        if self.params.get("REPO_INFO_PROMPT"):
            system_message = f"{system_message}\n{self.params['REPO_INFO_PROMPT']}"

        user_message = f"""
            1. Here's the information for the pull request you need to review:
            
            Pull Request Title:
            <pull_request_title>
            {self.params['PULL_REQUEST_TITLE']}
            </pull_request_title>
            
            Pull Request Description:
            <pull_request_description>
            {self.params['PULL_REQUEST_DESCRIPTION']}
            </pull_request_description>
            
            Pull Request Diff:
            <pull_request_diff>
            {self.params['PULL_REQUEST_DIFF']}
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
            
            Keep in mind these important instructions when reviewing the code:
            - Focus solely on major code communication issues as outlined above.
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
