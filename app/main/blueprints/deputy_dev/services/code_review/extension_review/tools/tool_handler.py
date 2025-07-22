from typing import Any, Dict, Optional
from app.main.blueprints.deputy_dev.services.code_review.extension_review.context.extension_context_service import (
    ExtensionContextService,
)
from app.main.blueprints.deputy_dev.services.code_review.common.review_planner.review_planner import ReviewPlanner

class ExtensionToolHandlers:
    """
    Handlers for the tools used in the code review flow.
    """

    @staticmethod
    async def handle_parse_final_response(
        tool_input: Dict[str, Any], context_service: Optional[ExtensionContextService] = None
    ) -> Dict[str, Any]:
        """
        Handle the parse_final_response tool request.

        Args:
            tool_input: The input for the tool.

        Returns:
            The tool response.
        """
        comments = tool_input.get("comments", [])
        summary = tool_input.get("summary", "")

        return {
            "comments": comments,
            "summary": summary,
        }

    @staticmethod
    async def handle_pr_review_planner(
        tool_input: Dict[str, Any], session_id: int, context_service: Optional[ExtensionContextService] = None
    ) -> Dict[str, Any]:
        """
        Handle the pr_review_planner tool request.

        Args:
            tool_input: The input for the tool.
            context_service: The context service instance.

        Returns:
            The tool response.
        """
        prompt_vars = {
            "PULL_REQUEST_TITLE": "NA",
            "PULL_REQUEST_DESCRIPTION": "NA",
            "PULL_REQUEST_DIFF": await context_service.get_pr_diff(append_line_no_info=True),
            "FOCUS_AREA": tool_input.get("review_focus", ""),
        }

        review_planner = ReviewPlanner(session_id=session_id, prompt_vars=prompt_vars)

        review_plan = await review_planner.get_review_plan()
        return review_plan
