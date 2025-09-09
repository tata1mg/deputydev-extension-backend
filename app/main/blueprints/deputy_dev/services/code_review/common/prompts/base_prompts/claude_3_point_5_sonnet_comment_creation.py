import re
import xml.etree.ElementTree as ET
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple

from app.backend_common.exception.exception import ParseException
from app.backend_common.utils.formatting import (
    format_code_blocks,
    format_comment_bucket_name,
)
from app.main.blueprints.deputy_dev.services.code_review.common.prompts.base_prompts.dataclasses.main import (
    LLMCommentData,
)
from deputydev_core.llm_handler.dataclasses.main import (
    NonStreamingResponse,
    StreamingResponse,
    UserAndSystemMessages,
)
from deputydev_core.llm_handler.models.dto.message_thread_dto import (
    MessageData,
    ToolUseRequestData,
)
from deputydev_core.llm_handler.providers.anthropic.prompts.base_prompts.base_claude_3_point_5_sonnet_prompt_handler import (
    BaseClaude3Point5SonnetPromptHandler,
)
from deputydev_core.utils.context_vars import get_context_value


class BaseClaude3Point5SonnetCommentCreationPrompt(BaseClaude3Point5SonnetPromptHandler):
    disable_tools = False
    disable_caching = False

    @classmethod
    def _parse_text_blocks(cls, text: str) -> Dict[str, List[LLMCommentData]]:
        review_content = None
        # Parse the XML string
        try:
            # Use regular expression to extract the content within <review> tags
            review_content = re.search(r"<review>.*?</review>", text, re.DOTALL)

            if review_content:
                xml_content = review_content.group(0)  # Extract matched XML content
                root = ET.fromstring(xml_content)

                comments: List[LLMCommentData] = []
                root_comments = root.find("comments")
                if root_comments is None:
                    raise ValueError("The XML string does not contain the expected <comments> tags.")

                for comment in root_comments.findall("comment"):
                    corrective_code_element = comment.find("corrective_code")
                    description_element = comment.find("description")
                    file_path_element = comment.find("file_path")
                    line_number_element = comment.find("line_number")
                    confidence_score_element = comment.find("confidence_score")
                    bucket_element = comment.find("bucket")

                    if (
                        description_element is None
                        or file_path_element is None
                        or line_number_element is None
                        or confidence_score_element is None
                        or bucket_element is None
                        or description_element.text is None
                        or file_path_element.text is None
                        or line_number_element.text is None
                        or confidence_score_element.text is None
                        or bucket_element.text is None
                    ):
                        raise ValueError("The XML string does not contain the expected comment elements.")

                    comments.append(
                        LLMCommentData(
                            comment=format_code_blocks(description_element.text),
                            corrective_code=(
                                corrective_code_element.text if corrective_code_element is not None else None
                            ),
                            file_path=file_path_element.text,
                            line_number=line_number_element.text,
                            confidence_score=float(confidence_score_element.text),
                            bucket=format_comment_bucket_name(bucket_element.text),
                        )
                    )
                return {"comments": comments}
            else:
                raise ValueError("The XML string does not contain the expected <review> tags.")

        except ET.ParseError as exception:
            raise ParseException(
                f"XML parsing error while decoding PR review comments data:  {text}, exception: {exception}"
            )

    @classmethod
    def get_parsed_result(cls, llm_response: NonStreamingResponse) -> List[Dict[str, List[LLMCommentData]]]:
        final_content = cls.get_parsed_response_blocks(llm_response.content)

        return final_content

    @classmethod
    def get_parsed_response_blocks(
        cls, response_block: List[MessageData]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        final_content: List[Dict[str, Any]] = []
        tool_use_map: Dict[str, Any] = {}
        for block in response_block:
            if isinstance(block, ToolUseRequestData):
                final_content.append(block)
                tool_use_map[block.content.tool_use_id] = ToolUseRequestData

        return final_content

    @classmethod
    async def get_parsed_streaming_events(cls, llm_response: StreamingResponse) -> AsyncIterator[Any]:
        raise NotImplementedError("Streaming is not supported for comments generation prompts")

    @classmethod
    def get_xml_review_comments_format(cls, bucket: str, agent_name: str, agent_focus_area: str = "") -> str:
        base_format = f"""<review>
            <comments>
            <comment>
            <description>Describe the {agent_focus_area} issue and make sure to enclose description within <![CDATA[ ]]> to avoid XML parsing errors. Don't provide any code block inside this field</description>"""

        if cls.is_corrective_code_enabled(agent_name=agent_name):
            base_format += """
            <corrective_code>Rewrite or create new (in case of missing) code, docstring or documentation for developer
            to directly use it.
            Add this section under <![CDATA[ ]]> for avoiding xml paring error.
            Set this value empty string if there is no suggestive code.
            </corrective_code>"""

        base_format += f"""
            <file_path>file path on which the comment is to be made</file_path>
            <line_number>line on which comment is relevant. get this value from `<>` block at each code start in input. Return the exact value present with label `+` or `-`</line_number>
            <confidence_score>floating point confidence score of the comment between 0.0 to 1.0  upto 2 decimal points</confidence_score>
            <bucket>
            {bucket}
            </bucket>
            </comment>
            <!-- Repeat the <comment> block for each {agent_focus_area} issue found -->
            </comments>
            </review>"""

        return base_format

    @classmethod
    def is_corrective_code_enabled(cls, agent_name: str) -> bool:
        agents_config = get_context_value("setting")["code_review_agent"]["agents"]

        return agents_config[agent_name].get("is_corrective_code_enabled", False)

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

                Pull Request Title:
                <pull_request_title>
                {params["PULL_REQUEST_TITLE"]}
                </pull_request_title>

                Pull Request Description:
                <pull_request_description>
                {params["PULL_REQUEST_DESCRIPTION"]}
                </pull_request_description>

                Pull Request Diff:
                <pull_request_diff>
                {params["PULL_REQUEST_DIFF"]}
                </pull_request_diff>
            """

    @classmethod
    def get_tools_specific_system_message(cls, params: Dict[str, Any]) -> str:
        system_message = """
        You are a senior developer tasked with reviewing pull requests for code quality issues.
        Your goal is to provide thorough, actionable feedback while maintaining efficiency and precision.
        
        # Parallel Tool Usage Guidelines
        - If multiple actions are needed,you can use tools in parallel per message to accomplish the task faster, with each tool use being informed by the result of the previous tool use. Do not assume the outcome of any tool use. Each step must be informed by the previous step's result.
        - If you choose to use the PR_REVIEW_PLANNER tool, you MUST NOT include any other tool calls in that same message.
        
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
    def get_tools_configurable_system_message(cls, params: Dict[str, Any]) -> str:
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

    @classmethod
    def get_force_finalize_user_message(cls) -> str:
        """
        Returns a strong final-instruction message for the PR review agent
        when the iteration limit is about to be reached.

        The message instructs the LLM to stop using any further tools and
        only call the `parse_final_Response` tool with the required comment structure.
        """
        return """
            You are a Pull Request reviewer agent. 
            With whatever information you currently have, review the diff now and provide final comments. 
            Do NOT call any more tools. 
            Only call the `parse_final_Response` tool, following its required comment structure.
        """

    def get_finalize_iteration_breached_prompt(self) -> Optional[UserAndSystemMessages]:
        return None
