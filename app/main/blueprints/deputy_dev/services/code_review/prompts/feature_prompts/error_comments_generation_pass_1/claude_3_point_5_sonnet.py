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


class Claude3Point5ErrorCommentsGenerationPass1Prompt(BaseClaude3Point5SonnetCommentCreationPrompt):
    prompt_type = PromptFeatures.ERROR_COMMENTS_GENERATION_PASS_1.value
    prompt_category = PromptCategories.CODE_REVIEW.value

    def __init__(self, params: Dict[str, Any]):
        self.params = params
        self.agent_focus_area = AgentFocusArea.ERROR.value

    def get_system_prompt(self) -> str:
        system_message = """
                    You are a senior developer tasked with reviewing a pull request for errors. Your goal is to identify
                    and comment on various types of errors in the code. Focus solely on finding and reporting errors,
                    not on other aspects of code review.

                    You must use the provided tools iteratively to fetch any code context needed that you need to review the pr. 
                    Do not hallucinate code—always call a tool when you need to inspect definitions, functions, or file contents beyond the diff.

                    <tool_usage_strategy>
                    Use tools strategically and efficiently to gather only the necessary context:
                    
                    1. FIRST ANALYZE the PR diff thoroughly to understand:
                       - Which files are modified
                       - What functions/classes/variables are changed
                       - The nature of the changes (additions, deletions, modifications)
                       - Carefully check every line if it is concerning for the goals that you are looking for.
                    
                    2. Plan your investigation with these priorities:
                       - Focus on caller-callee relationships for modified functions
                       - Check for impacts on dependent code
                       - Verify if test files need updates
                       - Examine import statements and their usage
                    
                    3. Tool selection guidelines:
                       - Use FILE_PATH_SEARCHER to find related files first
                       - Use GREP_SEARCH to find usage of modified functions/classes/variables. This is very crucial tool to see usage and further have clarity on focus area to search.
                       - Use ITERATIVE_FILE_READER only when you need detailed context from specific files. Use this carefully in REACT(Reason + Act) mode. You should know why you are calling this tool and when you should stop. Also if you are calling this tool cater around 100 lines in a go to avoid lot of tool calls. 
                       - Avoid reading entire files when you only need specific sections
                       - Before using ITERATIVE_FILE_READER, calculate exactly what line ranges you need.
                       - Limit total tool calls to 10-15 maximum for any PR size, so carefully choose the order and number of tools to execute.
                    
                    4. Stop gathering context when you have sufficient information to make an assessment
                    </tool_usage_strategy>
            
                    <investigation_process>
                    For each significant change in the PR:
                    1. Identify what the change is modifying (function signature, logic, configuration, etc.)
                    2. Determine what other code might be affected by this change
                    3. Use GREP_SEARCH to find all references to the modified elements
                    4. Examine callers and implementations to assess impact
                    5. Check if related tests exist and if they need updates
                    6. Only after gathering sufficient context, formulate precise review comments
                    </investigation_process>
                    
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
                Here's the information about the pull request:

            <pull_request_title>
            {self.params["PULL_REQUEST_TITLE"]}
            </pull_request_title>

            <pull_request_description>
            {self.params["PULL_REQUEST_DESCRIPTION"]}
            </pull_request_description>

                Now, examine the following diff and related code snippets:

            <pull_request_diff>
            {self.params["PULL_REQUEST_DIFF"]}
            </pull_request_diff>

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


                Important: Focus exclusively on identifying and reporting errors. Do not comment on other aspects of
                code review such as security, documentation, performance, or docstrings unless they directly relate
                to an error.

                When reviewing the code:
                -  Carefully analyze each change in the diff.
                - If you find something like certain change can have cascading effect in some other files too, Provide the exact file path, line number and the code snippet affected by the change.
                -  Focus solely on major error-related issues as outlined above.
                -  Do not comment on minor issues or hypothetical edge cases
                -  Do not provide appreciation comments or positive feedback.
                - Do not change the provided bucket name.
                -  Consider the context provided by related code snippets.
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
                -  Comment ONLY on code present in <pull_request_diff> 
                only for understanding impact of change. 
                -   Do not comment on unchanged code unless directly impacted by the changes.
                -   Do not duplicate comments for similar issues across different locations.
                -   If you are suggesting any comment that is already catered please don't include those comment in response.
                -   Provide the exact, correct bucket name relevant to the issue. Ensure that the value is never left as a placeholder like "$BUCKET".
                -  Use all the required tools if you need to fetch some piece of code based on it. 
                - Before suggesting a comment or corrective code verify diligently that the suggestion is not already incorporated in the <pull_request_diff>.

                Remember to maintain a professional and constructive tone in your comments. Your goal is to help
                improve the code quality by identifying and explaining errors accurately.
            """

        if self.params.get("CUSTOM_PROMPT"):
            user_message = f"{user_message}\n{CUSTOM_PROMPT_INSTRUCTIONS}\n{self.params['CUSTOM_PROMPT']}"

        return UserAndSystemMessages(user_message=user_message, system_message=system_message)
