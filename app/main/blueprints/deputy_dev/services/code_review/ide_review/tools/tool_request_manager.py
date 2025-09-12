import json
from typing import Any, Dict, List, Optional

from deputydev_core.llm_handler.dataclasses.main import ConversationTool
from deputydev_core.llm_handler.models.dto.message_thread_dto import (
    ContentBlockCategory,
    ToolUseRequestData,
)
from deputydev_core.utils.app_logger import AppLogger

from app.backend_common.utils.formatting import (
    format_code_blocks,
    format_comment_bucket_name,
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
from app.main.blueprints.deputy_dev.services.code_review.common.tools.pr_review_planner import PR_REVIEW_PLANNER
from app.main.blueprints.deputy_dev.services.code_review.ide_review.comments.dataclasses.main import (
    LLMCommentData,
)
from app.main.blueprints.deputy_dev.services.code_review.ide_review.context.ide_review_context_service import (
    IdeReviewContextService,
)
from app.main.blueprints.deputy_dev.services.code_review.ide_review.tools.parse_final_response import (
    PARSE_FINAL_RESPONSE,
)
from app.main.blueprints.deputy_dev.services.code_review.ide_review.tools.tool_handler import (
    ExtensionToolHandlers,
)


class ToolRequestManager:
    """
    Simplified tool request manager designed specifically for single-iteration flow.
    This manager handles tool parsing and execution for the extension review system.
    """

    def __init__(self, context_service: IdeReviewContextService) -> None:
        self.context_service = context_service
        self.tools = [
            GREP_SEARCH,
            ITERATIVE_FILE_READER,
            FILE_PATH_SEARCHER,
            PARSE_FINAL_RESPONSE,
            PR_REVIEW_PLANNER,
        ]

    def get_tools(self) -> List[ConversationTool]:
        """
        Get the list of tools available for the extension review flow.
        """
        return self.tools

    def parse_tool_use_request(self, llm_response: Any) -> Optional[Dict[str, Any]]:
        """
        Parse and return tool use request details for regular tools (excluding special tools).

        Args:
            llm_response: The LLM response containing the tool use request.

        Returns:
            Dictionary with tool request details if a regular tool was requested, None otherwise.
        """
        if not hasattr(llm_response, "parsed_content") or not llm_response.parsed_content:
            return None

        for content_block in llm_response.parsed_content:
            if hasattr(content_block, "type") and content_block.type == ContentBlockCategory.TOOL_USE_REQUEST:
                tool_use_request = content_block
                if not isinstance(tool_use_request, ToolUseRequestData):
                    continue

                tool_name = tool_use_request.content.tool_name
                tool_input = tool_use_request.content.tool_input
                tool_use_id = tool_use_request.content.tool_use_id

                # Skip special tools that are handled immediately
                if tool_name in ["parse_final_response", "pr_review_planner"]:
                    return None

                # Return details for regular tools that need frontend processing
                return {
                    "type": "tool_use_request",
                    "tool_name": tool_name,
                    "tool_input": tool_input,
                    "tool_use_id": tool_use_id,
                }

        return None

    def is_final_response(self, llm_response: Any) -> bool:
        """
        Check if the LLM response contains a parse_final_response tool use.
        """
        return self._has_tool_use(llm_response, "parse_final_response")

    def is_review_planner_response(self, llm_response: Any) -> bool:
        """
        Check if the LLM response contains a pr_review_planner tool use.
        """
        return self._has_tool_use(llm_response, "pr_review_planner")

    def _has_tool_use(self, llm_response: Any, tool_name: str) -> bool:
        """
        Check if the LLM response contains a specific tool use.
        """
        if not hasattr(llm_response, "parsed_content") or not llm_response.parsed_content:
            return False

        for content_block in llm_response.parsed_content:
            if (
                hasattr(content_block, "type")
                and content_block.type == ContentBlockCategory.TOOL_USE_REQUEST
                and isinstance(content_block, ToolUseRequestData)
                and content_block.content.tool_name == tool_name
            ):
                return True

        return False

    def extract_final_response(self, llm_response: Any) -> Dict[str, Any]:
        """
        Extract and parse the final response containing comments.
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
                return self._parse_comments_from_tool_input(content_block.content.tool_input)

        return {}

    async def process_review_planner_response(self, llm_response: Any, session_id: int) -> Dict[str, Any] | None:
        """
        Process the review planner response and return the review plan.
        """
        if not self.is_review_planner_response(llm_response):
            return None

        for content_block in llm_response.parsed_content:
            if (
                hasattr(content_block, "type")
                and content_block.type == ContentBlockCategory.TOOL_USE_REQUEST
                and isinstance(content_block, ToolUseRequestData)
                and content_block.content.tool_name == "pr_review_planner"
            ):
                tool_input = content_block.content.tool_input
                return await ExtensionToolHandlers.handle_pr_review_planner(
                    tool_input, session_id, self.context_service
                )

        return None

    def _parse_comments_from_tool_input(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse comments from the parse_final_response tool input.
        """
        comments: List[LLMCommentData] = []
        llm_comments = tool_input.get("comments")

        if llm_comments is None:
            raise ValueError(
                f"The parse_final_tool_response does not contain any comments array: tool_input: {json.dumps(tool_input, indent=2)}"
            )

        for comment in llm_comments:
            required_fields = [
                "title",
                "tag",
                "description",
                "file_path",
                "line_number",
                "confidence_score",
                "bucket",
                "rationale",
            ]
            for field in required_fields:
                if comment.get(field) is None:
                    raise ValueError(f"The comment is missing required field: {field}")

            try:
                comments.append(
                    LLMCommentData(
                        title=comment.get("title"),
                        tag=comment.get("tag"),
                        comment=format_code_blocks(comment["description"]),
                        corrective_code=comment.get("corrective_code"),
                        file_path=comment["file_path"],
                        line_number=comment["line_number"],
                        confidence_score=float(comment["confidence_score"]),
                        bucket=format_comment_bucket_name(comment["bucket"]),
                        rationale=comment["rationale"],
                    )
                )
            except (ValueError, TypeError) as e:
                AppLogger.log_warn(f"Comment Validation Faileds: {comment}: {e}")
                continue

        return {"comments": comments}
