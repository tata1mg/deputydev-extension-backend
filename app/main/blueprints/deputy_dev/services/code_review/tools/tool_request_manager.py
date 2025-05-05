from typing import Any, Dict, List, Optional

from app.backend_common.models.dto.message_thread_dto import (
    ContentBlockCategory,
    MessageThreadDTO,
    ToolUseRequestContent,
    ToolUseRequestData,
    ToolUseResponseContent,
    ToolUseResponseData,
)
from app.backend_common.services.llm.dataclasses.main import ConversationTool
from app.main.blueprints.deputy_dev.services.code_review.tools.parse_final_response import PARSE_FINAL_RESPONSE
from app.main.blueprints.deputy_dev.services.code_review.tools.tool_handlers import ToolHandlers
from app.main.blueprints.one_dev.services.query_solver.tools.file_path_searcher import FILE_PATH_SEARCHER
from app.main.blueprints.one_dev.services.query_solver.tools.focused_snippets_searcher import (
    FOCUSED_SNIPPETS_SEARCHER,
)
from app.main.blueprints.one_dev.services.query_solver.tools.grep_search import GREP_SEARCH
from app.main.blueprints.one_dev.services.query_solver.tools.iterative_file_reader import (
    ITERATIVE_FILE_READER,
)
from app.main.blueprints.one_dev.services.query_solver.tools.related_code_searcher import (
    RELATED_CODE_SEARCHER,
)
from app.main.blueprints.deputy_dev.services.code_review.prompts.base_prompts.dataclasses.main import (
    LLMCommentData,
)
from app.backend_common.utils.formatting import (
    format_code_blocks,
    format_comment_bucket_name,
)


class ToolRequestManager:
    """
    Manages tool requests and responses for the code review flow.
    """

    def __init__(self):
        self.tools = [
            RELATED_CODE_SEARCHER,
            GREP_SEARCH,
            ITERATIVE_FILE_READER,
            FOCUSED_SNIPPETS_SEARCHER,
            FILE_PATH_SEARCHER,
            PARSE_FINAL_RESPONSE,
        ]

    def get_tools(self) -> List[ConversationTool]:
        """
        Get the list of tools available for the code review flow.
        """
        return self.tools

    async def process_tool_use_request(
        self, llm_response: Any, session_id: int
    ) -> Optional[ToolUseResponseData]:
        """
        Process a tool use request from the LLM response.
        
        Args:
            llm_response: The LLM response containing the tool use request.
            session_id: The session ID.
            
        Returns:
            The tool use response data if a tool was used, None otherwise.
        """
        if not hasattr(llm_response, "parsed_content") or not llm_response.parsed_content:
            return None

        for content_block in llm_response.parsed_content:
            # if content_block.get("type") == "TOOL_USE_REQUEST_BLOCK":
            if (
                hasattr(content_block, "type")
                and content_block.type == ContentBlockCategory.TOOL_USE_REQUEST
            ):
                tool_use_request = content_block
                if not isinstance(tool_use_request, ToolUseRequestData):
                    continue

                tool_name = tool_use_request.content.tool_name
                tool_input = tool_use_request.content.tool_input
                tool_use_id = tool_use_request.content.tool_use_id

                # Process the tool request based on the tool name
                print("*****************Tool Call*****************")
                print(tool_input)
                tool_response = await self._process_tool_request(tool_name, tool_input, session_id)

                if tool_response is not None:
                    return ToolUseResponseData(
                        content=ToolUseResponseContent(
                            tool_name=tool_name,
                            tool_use_id=tool_use_id,
                            response=tool_response,
                        )
                    )

        return None

    async def _process_tool_request(self, tool_name: str, tool_input: Dict[str, Any], session_id: int) -> Optional[Dict[str, Any]]:
        """
        Process a tool request based on the tool name.
        
        Args:
            tool_name: The name of the tool.
            tool_input: The input for the tool.
            session_id: The session ID.
            
        Returns:
            The tool response if the tool was processed, None otherwise.
        """
        # Call the appropriate tool handler based on the tool name
        if tool_name == "related_code_searcher":
            return await ToolHandlers.handle_related_code_searcher(tool_input)
        elif tool_name == "grep_search":
            return await ToolHandlers.handle_grep_search(tool_input)
        elif tool_name == "iterative_file_reader":
            return await ToolHandlers.handle_iterative_file_reader(tool_input)
        elif tool_name == "focused_snippets_searcher":
            return await ToolHandlers.handle_focused_snippets_searcher(tool_input)
        elif tool_name == "file_path_searcher":
            return await ToolHandlers.handle_file_path_searcher(tool_input)
        elif tool_name == "parse_final_response":
            return await ToolHandlers.handle_parse_final_response(tool_input)
        
        return None

    def is_final_response(self, llm_response: Any) -> bool:
        """
        Check if the LLM response is a final response (contains a parse_final_response tool use).
        
        Args:
            llm_response: The LLM response.
            
        Returns:
            True if the response is a final response, False otherwise.
        """
        if not hasattr(llm_response, "parsed_content") or not llm_response.parsed_content:
            return False

        for content_block in llm_response.parsed_content:
            if (
                hasattr(content_block, "type")
                and content_block.type == ContentBlockCategory.TOOL_USE_REQUEST
                and isinstance(content_block, ToolUseRequestData)
                and content_block.content.tool_name == "parse_final_response"
            ):
                return True

        return False

    def extract_final_response(self, llm_response: Any) -> Dict[str, Any]:
        """
        Extract the final response from the LLM response.
        
        Args:
            llm_response: The LLM response.
            
        Returns:
            The final response.
        """
        if not self.is_final_response(llm_response):
            return {}

        for content_block in llm_response.parsed_content:
            if (
                hasattr(content_block, "type")
                and content_block.type == ContentBlockCategory.TOOL_USE_REQUEST
                and isinstance(content_block, ToolUseRequestData)
                and content_block.content.tool_name == "parse_final_response"
            ):
                comments: List[LLMCommentData] = []
                llm_comments = content_block.content.tool_input.get("comments")
                for comment in llm_comments:
                    corrective_code_element = comment.get("corrective_code")
                    description_element = comment.get("description")
                    file_path_element = comment.get("file_path")
                    line_number_element = comment.get("line_number")
                    confidence_score_element = comment.get("confidence_score")
                    bucket_element = comment.get("bucket")

                    if (
                        description_element is None
                        or file_path_element is None
                        or line_number_element is None
                        or confidence_score_element is None
                        or bucket_element is None
                    ):
                        raise ValueError("The Response does not contain the expected comment elements.")

                    comments.append(
                        LLMCommentData(
                            comment=format_code_blocks(description_element),
                            corrective_code=corrective_code_element
                            if corrective_code_element is not None
                            else None,
                            file_path=file_path_element,
                            line_number=line_number_element,
                            confidence_score=float(confidence_score_element),
                            bucket=format_comment_bucket_name(bucket_element),
                        )
                    )
                return {"comments": comments}

        return {} 