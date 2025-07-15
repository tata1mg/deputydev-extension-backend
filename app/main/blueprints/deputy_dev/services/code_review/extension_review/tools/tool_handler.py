import os
from concurrent.futures import ProcessPoolExecutor
from typing import Any, Dict, Optional

from deputydev_core.services.embedding.pr_review_embedding_manager import (
    PRReviewEmbeddingManager,
)
from deputydev_core.services.initialization.review_initialization_manager import (
    ReviewInitialisationManager,
)
from deputydev_core.services.tools.file_path_search.dataclass.main import (
    FilePathSearchPayload,
)
from deputydev_core.services.tools.file_path_search.file_path_search import (
    FilePathSearch,
)
from deputydev_core.services.tools.focussed_snippet_search.dataclass.main import (
    FocussedSnippetSearchParams,
)
from deputydev_core.services.tools.focussed_snippet_search.focussed_snippet_search import (
    FocussedSnippetSearch,
)
from deputydev_core.services.tools.grep_search.dataclass.main import (
    GrepSearchRequestParams,
)
from deputydev_core.services.tools.grep_search.grep_search import GrepSearch
from deputydev_core.services.tools.iterative_file_reader.dataclass.main import (
    IterativeFileReaderRequestParams,
)
from deputydev_core.services.tools.iterative_file_reader.iterative_file_reader import (
    IterativeFileReader,
)
from deputydev_core.services.tools.relevant_chunks.dataclass.main import (
    RelevantChunksParams,
)
from deputydev_core.services.tools.relevant_chunks.relevant_chunk import RelevantChunks
from deputydev_core.utils.config_manager import ConfigManager
from deputydev_core.utils.constants.enums import ContextValueKeys
from deputydev_core.utils.context_vars import get_context_value

from app.main.blueprints.deputy_dev.client.one_dev_review_client import (
    OneDevReviewClient,
)
from app.main.blueprints.deputy_dev.services.code_review.extension_review.context.extension_context_service import (
    ExtensionContextService,
)
from app.main.blueprints.deputy_dev.services.code_review.common.review_planner.review_planner import ReviewPlanner
from app.main.blueprints.deputy_dev.services.code_review.common.utils.weaviate_client import get_weaviate_connection


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
            "PULL_REQUEST_TITLE": "",
            "PULL_REQUEST_DESCRIPTION": "",
            "PULL_REQUEST_DIFF": await context_service.get_pr_diff(append_line_no_info=True),
            "FOCUS_AREA": tool_input.get("review_focus", ""),
        }

        review_planner = ReviewPlanner(session_id=session_id, prompt_vars=prompt_vars)

        review_plan = await review_planner.get_review_plan()
        return review_plan
