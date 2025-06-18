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
from app.main.blueprints.deputy_dev.services.code_review.context.context_service import ContextService
from app.main.blueprints.deputy_dev.services.code_review.review_planner.review_planner import ReviewPlanner
from app.main.blueprints.deputy_dev.services.code_review.utils.weaviate_client import get_weaviate_connection


class ToolHandlers:
    """
    Handlers for the tools used in the code review flow.
    """

    @staticmethod
    async def handle_related_code_searcher(
        tool_input: Dict[str, Any], context_service: Optional[ContextService] = None
    ) -> Dict[str, Any]:
        """
        Handle the related_code_searcher tool request.

        Args:
            tool_input: The input for the tool.

        Returns:
            The tool response.
        """
        payload = {
            "repo_path": get_context_value("repo_path"),
            "query": tool_input["search_query"],
            "session_id": get_context_value("session_id"),
            "session_type": "PR_REVIEW",
        }
        payload = RelevantChunksParams(**payload)
        one_dev_review_client = OneDevReviewClient()
        embedding_manager = PRReviewEmbeddingManager(
            auth_token_key=ContextValueKeys.PR_REVIEW_TOKEN.value, one_dev_client=one_dev_review_client
        )
        with ProcessPoolExecutor(max_workers=ConfigManager.configs["NUMBER_OF_WORKERS"]) as executor:
            weaviate_client = await get_weaviate_connection()
            initialisation_manager = ReviewInitialisationManager(
                repo_path=payload.repo_path,
                process_executor=executor,
                one_dev_client=one_dev_review_client,
                weaviate_client=weaviate_client,
            )

            chunks = await RelevantChunks(payload.repo_path).get_relevant_chunks(
                payload,
                one_dev_review_client,
                embedding_manager,
                initialisation_manager,
                executor,
                ContextValueKeys.PR_REVIEW_TOKEN.value,
            )
        return chunks

    @staticmethod
    async def handle_grep_search(
        tool_input: Dict[str, Any], context_service: Optional[ContextService] = None
    ) -> Dict[str, Any]:
        """
        Handle the grep_search tool request.

        Args:
            tool_input: The input for the tool.

        Returns:
            The tool response.
        """
        tool_input["repo_path"] = get_context_value("repo_path")
        if isinstance(tool_input["search_terms"], str):
            tool_input["search_terms"] = [tool_input["search_terms"]]
        payload = GrepSearchRequestParams(**tool_input)
        grep_search_results = await GrepSearch(repo_path=payload.repo_path).perform_grep_search(
            directory_path=payload.directory_path,
            search_terms=payload.search_terms,
        )

        response = {
            "data": [
                {
                    "chunk_info": chunk["chunk_info"].model_dump(mode="json"),  # type: ignore
                    "matched_line": chunk["matched_line"],
                }
                for chunk in grep_search_results
            ],
        }
        return response

    @staticmethod
    async def handle_iterative_file_reader(
        tool_input: Dict[str, Any], context_service: Optional[ContextService] = None
    ) -> Dict[str, Any]:
        """
        Handle the iterative_file_reader tool request.

        Args:
            tool_input: The input for the tool.
            session_id: The session ID.

        Returns:
            The tool response.
        """
        tool_input["repo_path"] = get_context_value("repo_path")
        payload = IterativeFileReaderRequestParams(**tool_input)
        file_content, eof_reached = await IterativeFileReader(
            file_path=os.path.join(payload.repo_path, payload.file_path)
        ).read_lines(start_line=payload.start_line, end_line=payload.end_line)
        response = {
            "data": {
                "chunk": file_content.model_dump(mode="json"),
                "eof_reached": eof_reached,
            },
        }
        return response

    @staticmethod
    async def handle_focused_snippets_searcher(
        tool_input: Dict[str, Any], context_service: Optional[ContextService] = None
    ) -> Dict[str, Any]:
        """
        Handle the focused_snippets_searcher tool request.

        Args:
            tool_input: The input for the tool.
            session_id: The session ID.

        Returns:
            The tool response.
        """
        tool_input["repo_path"] = get_context_value("repo_path")
        payload = FocussedSnippetSearchParams(**tool_input)
        weaviate_client = await get_weaviate_connection()
        one_dev_client = OneDevReviewClient()
        with ProcessPoolExecutor(max_workers=ConfigManager.configs["NUMBER_OF_WORKERS"]) as executor:
            initialisation_manager = ReviewInitialisationManager(
                repo_path=payload.repo_path, process_executor=executor, one_dev_client=one_dev_client
            )
            chunks = await FocussedSnippetSearch.search_code(payload, weaviate_client, initialisation_manager)
        return chunks

    @staticmethod
    async def handle_file_path_searcher(
        tool_input: Dict[str, Any], context_service: Optional[ContextService] = None
    ) -> Dict[str, Any]:
        """
        Handle the file_path_searcher tool request.

        Args:
            tool_input: The input for the tool.

        Returns:
            The tool response.
        """
        tool_input["repo_path"] = get_context_value("repo_path")
        payload = FilePathSearchPayload(**tool_input)
        files = FilePathSearch(repo_path=payload.repo_path).list_files(
            directory=payload.directory,
            search_terms=payload.search_terms,
        )
        response = {
            "data": files,
        }
        return response

    @staticmethod
    async def handle_parse_final_response(
        tool_input: Dict[str, Any], context_service: Optional[ContextService] = None
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
        tool_input: Dict[str, Any], context_service: Optional[ContextService] = None
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
            "PULL_REQUEST_TITLE": context_service.get_pr_title(),
            "PULL_REQUEST_DESCRIPTION": context_service.get_pr_description(),
            "PULL_REQUEST_DIFF": await context_service.get_pr_diff(append_line_no_info=True),
            "FOCUS_AREA": tool_input.get("review_focus", ""),
        }

        review_planner = ReviewPlanner(session_id=get_context_value("session_id"), prompt_vars=prompt_vars)

        review_plan = await review_planner.get_review_plan()
        return review_plan
