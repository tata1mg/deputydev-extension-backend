import json
from typing import Any, Awaitable, Callable, Dict, List

from deputydev_core.llm_handler.dataclasses.main import ConversationTool, NonStreamingParsedLLMCallResponse
from deputydev_core.llm_handler.models.dto.message_thread_dto import (
    ContentBlockCategory,
    ToolUseRequestData,
    ToolUseResponseContent,
    ToolUseResponseData,
)
from deputydev_core.utils.app_logger import AppLogger

from app.backend_common.utils.formatting import (
    format_code_blocks,
    format_comment_bucket_name,
)
from app.main.blueprints.deputy_dev.services.code_review.common.prompts.base_prompts.dataclasses.main import (
    LLMCommentData,
)
from app.main.blueprints.deputy_dev.services.code_review.common.tools.constants.tools_fallback import (
    EXCEPTION_RAISED_FALLBACK,
)
from app.main.blueprints.deputy_dev.services.code_review.common.tools.file_path_searcher import (
    FILE_PATH_SEARCHER,
)
from app.main.blueprints.deputy_dev.services.code_review.common.tools.grep_search import (
    GREP_SEARCH,
)
from app.main.blueprints.deputy_dev.services.code_review.common.tools.iterative_file_reader import (
    ITERATIVE_FILE_READER,
)
from app.main.blueprints.deputy_dev.services.code_review.common.tools.parse_final_response import (
    PARSE_FINAL_RESPONSE,
)
from app.main.blueprints.deputy_dev.services.code_review.common.tools.pr_review_planner import PR_REVIEW_PLANNER
from app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers import (
    ToolHandlers,
)
from app.main.blueprints.deputy_dev.services.code_review.vcs_review.context.context_service import ContextService


class ToolRequestManager:
    """
    Manages tool requests and responses for the code review flow.
    """

    def __init__(self, context_service: ContextService) -> None:
        self.context_service = context_service
        self.tools = [
            # RELATED_CODE_SEARCHER,
            GREP_SEARCH,
            ITERATIVE_FILE_READER,
            # FOCUSED_SNIPPETS_SEARCHER,
            FILE_PATH_SEARCHER,
            PARSE_FINAL_RESPONSE,
            PR_REVIEW_PLANNER,
        ]
        self._tool_handlers: Dict[str, Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]] = {
            "related_code_searcher": ToolHandlers.handle_related_code_searcher,
            "grep_search": ToolHandlers.handle_grep_search,
            "iterative_file_reader": ToolHandlers.handle_iterative_file_reader,
            "focused_snippets_searcher": ToolHandlers.handle_focused_snippets_searcher,
            "file_path_searcher": ToolHandlers.handle_file_path_searcher,
            "parse_final_response": ToolHandlers.handle_parse_final_response,
            "pr_review_planner": ToolHandlers.handle_pr_review_planner,
        }

    def get_tools(self) -> List[ConversationTool]:
        """
        Get the list of tools available for the code review flow.
        """
        return self.tools

    def get_tool_use_request_data(
        self, llm_response: NonStreamingParsedLLMCallResponse, session_id: int
    ) -> List[ToolUseRequestData]:
        tool_use_requests: List[ToolUseRequestData] = []
        for content_block in llm_response.parsed_content:
            if hasattr(content_block, "type") and content_block.type == ContentBlockCategory.TOOL_USE_REQUEST:
                tool_use_request = content_block
                if not isinstance(tool_use_request, ToolUseRequestData):
                    continue
                tool_use_requests.append(tool_use_request)
        return tool_use_requests

    async def process_tool_use_request(self, llm_response: Any, session_id: int) -> List[ToolUseResponseData]:
        """
        Process a tool use request from the LLM response.

        Args:
            llm_response: The LLM response containing the tool use request.
            session_id: The session ID.

        Returns:
            The tool use response data if a tool was used, None otherwise.
        """

        tool_responses: List[ToolUseResponseData] = []
        for content_block in llm_response.parsed_content:
            if hasattr(content_block, "type") and content_block.type == ContentBlockCategory.TOOL_USE_REQUEST:
                tool_use_request = content_block
                if not isinstance(tool_use_request, ToolUseRequestData):
                    continue

                tool_name = tool_use_request.content.tool_name
                tool_input = tool_use_request.content.tool_input
                tool_use_id = tool_use_request.content.tool_use_id

                # Process the tool request based on the tool name
                try:
                    tool_response = await self._process_tool_request(tool_name, tool_input)
                except Exception as e:  # noqa: BLE001
                    AppLogger.log_error(f"Error processing tool {tool_name}: {e}")
                    tool_response = EXCEPTION_RAISED_FALLBACK.format(
                        tool_name=tool_name, tool_input=json.dumps(tool_input, indent=2), error_message=str(e)
                    )

                tool_responses.append(
                    ToolUseResponseData(
                        content=ToolUseResponseContent(
                            tool_name=tool_name,
                            tool_use_id=tool_use_id,
                            response=tool_response,
                        )
                    )
                )
        return tool_responses

    async def _process_tool_request(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        handler = self._tool_handlers.get(tool_name)
        if handler:
            return await handler(tool_input, self.context_service)
        raise Exception(f"No such Tool Exists: tool_name: {tool_name}")

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

    def extract_final_response(self, llm_response: NonStreamingParsedLLMCallResponse) -> Dict[str, Any]:
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
                if llm_comments is None:
                    raise ValueError(
                        f"The parse_final_tool_response does not contain any comments array: tool_input: {json.dumps(content_block.content.tool_input, indent=2)}"
                    )
                for comment in llm_comments:
                    corrective_code_element = comment.get("corrective_code")
                    description_element = comment.get("description")
                    file_path_element = comment.get("file_path")
                    line_number_element = comment.get("line_number")
                    confidence_score_element = comment.get("confidence_score")
                    bucket_element = comment.get("bucket")
                    rationale = comment.get("rationale")

                    if (
                        description_element is None
                        or file_path_element is None
                        or line_number_element is None
                        or confidence_score_element is None
                        or bucket_element is None
                        or rationale is None
                    ):
                        raise ValueError("The Response does not contain the expected comment elements.")

                    comments.append(
                        LLMCommentData(
                            comment=format_code_blocks(description_element),
                            corrective_code=corrective_code_element if corrective_code_element is not None else None,
                            file_path=file_path_element,
                            line_number=line_number_element,
                            confidence_score=float(confidence_score_element),
                            bucket=format_comment_bucket_name(bucket_element),
                            rationale=rationale,
                        )
                    )
                return {"comments": comments}

        return {}
