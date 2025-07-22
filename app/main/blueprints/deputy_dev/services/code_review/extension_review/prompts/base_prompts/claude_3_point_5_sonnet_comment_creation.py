from typing import Any, Dict


from app.main.blueprints.deputy_dev.services.code_review.common.prompts.base_prompts.claude_3_point_5_sonnet_comment_creation import BaseClaude3Point5SonnetCommentCreationPrompt as CommonBaseClaude3Point5SonnetCommentCreationPrompt


class BaseClaude3Point5SonnetCommentCreationPrompt(CommonBaseClaude3Point5SonnetCommentCreationPrompt):
    disable_tools = False
    disable_caching = False


    @classmethod
    def get_user_cached_message_template(cls, params: Dict[str, Any]) -> str:
        """Get the cached message template for PR review.

        Args:
            params: Dictionary containing PR information

        Returns:
            str: Formatted cached message template
        """
        return f"""
                Here's the information for the pull request you need to review:
                Pull Request Diff:
                <pull_request_diff>
                {params["PULL_REQUEST_DIFF"]}
                </pull_request_diff>
            """

    @classmethod
    def get_tools_specific_system_message(cls, params):
        system_message = """
        You are a senior developer tasked with reviewing pull requests for code quality issues.
        Your goal is to provide thorough, actionable feedback while maintaining efficiency and precision.

        <tool_usage_strategy>
        Use tools strategically and efficiently to gather only the necessary context:

        1. FIRST ANALYZE the PR diff thoroughly to understand:
           - Which files are modified
           - What functions/classes/variables are changed
           - The nature of the changes (additions, deletions, modifications)
           - Carefully check every line for issues relevant to your review focus

        2. Plan your investigation with these priorities:
           - Focus on caller-callee relationships for modified functions
           - Check for impacts on dependent code
           - Verify if test files need updates
           - Examine import statements and their usage

        3. Tool selection guidelines:
           - Use PR_REVIEW_PLANNER to create an investigation plan
           - Use FILE_PATH_SEARCHER to locate relevant files
           - Use GREP_SEARCH to find usage patterns with precise terms
           - Use ITERATIVE_FILE_READER only for detailed implementation analysis
           - Read larger sections of files at once (50-100 lines) to reduce calls
           - Avoid reading entire files when you only need specific sections

        4. Stop gathering context when you have sufficient information to make an assessment
        5. Limit total tool calls to 8-10 maximum for any PR size
        6. Prioritize high-impact changes over minor style issues
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
        - If any change has impacting change in other files, function, class where it was used, provide the exact impacting areas in comment description.
        - Do not hallucinate code—always call a tool when you need to inspect definitions, functions, or file contents beyond the diff.
        """

        if params.get("REPO_INFO_PROMPT"):
            system_message = f"{system_message}\n{params['REPO_INFO_PROMPT']}"

        return system_message

    @classmethod
    def get_tools_configurable_system_message(cls, params) -> str:
        system_message = """
        You are a senior developer tasked with reviewing pull requests for code quality issues.
        Your goal is to provide thorough, actionable feedback while maintaining efficiency and precision.
        """

        if not cls.disable_tools:
            system_message += """
            <tool_usage_strategy>
            Use tools strategically and efficiently to gather only the necessary context:

            1. FIRST ANALYZE the PR diff thoroughly to understand:
               - Which files are modified
               - What functions/classes/variables are changed
               - The nature of the changes (additions, deletions, modifications)
               - Carefully check every line for issues relevant to your review focus

            2. Plan your investigation with these priorities:
               - Focus on caller-callee relationships for modified functions
               - Check for impacts on dependent code
               - Verify if test files need updates
               - Examine import statements and their usage

            3. Tool selection guidelines:
               - Use PR_REVIEW_PLANNER to create an investigation plan
               - Use FILE_PATH_SEARCHER to locate relevant files
               - Use GREP_SEARCH to find usage patterns with precise terms
               - Use ITERATIVE_FILE_READER only for detailed implementation analysis
               - Read larger sections of files at once (50-100 lines) to reduce calls
               - Avoid reading entire files when you only need specific sections

            4. Stop gathering context when you have sufficient information to make an assessment
            5. Limit total tool calls to 10-15 maximum for any PR size
            </tool_usage_strategy>
            """

        system_message += """

        IMPORTANT:
        - You MUST ALWAYS use the parse_final_response tool to deliver your final review comments.
        Never provide review comments as plain text in your response. All final reviews MUST be delivered
        through the parse_final_response tool inside a tool use block.
        - If any change has impacting change in other files, function, class where it was used, provide the exact impacting areas in comment description.
        """

        if params.get("REPO_INFO_PROMPT"):
            system_message = f"{system_message}\n{params['REPO_INFO_PROMPT']}"

        return system_message
