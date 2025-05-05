from typing import Any, Dict
import os
from deputydev_core.services.embedding.pr_review_embedding_manager import PRReviewEmbeddingManager
from deputydev_core.services.file_path_search.file_path_search_service import FilePathSearchService
from deputydev_core.services.grep_search.dataclass.main import GrepSearchRequestParams
from deputydev_core.services.grep_search.grep_search_service import GrepSearchService
from deputydev_core.services.iterative_file_reader.dataclass.main import IterativeFileReaderRequestParams
from deputydev_core.services.iterative_file_reader.iterative_file_reader import IterativeFileReader
from deputydev_core.services.relevant_chunks.dataclass.main import RelevantChunksParams
from deputydev_core.services.relevant_chunks.relevant_chunk_service import RelevantChunksService

from deputydev_core.utils.config_manager import ConfigManager
from deputydev_core.services.batch_chunk_search.dataclass.main import BatchSearchParams
from deputydev_core.services.batch_chunk_search.batch_chunk_search_service import BatchSearchService
from deputydev_core.utils.weaviate import weaviate_connection
from deputydev_core.services.initialization.review_initialization_manager import ReviewInitialisationManager
from deputydev_core.services.file_path_search.dataclass.main import FilePathSearchPayload
from app.main.blueprints.deputy_dev.client.one_dev_review_client import OneDevReviewClient
from concurrent.futures import ProcessPoolExecutor
from deputydev_core.utils.context_vars import get_context_value


class ToolHandlers:
    """
    Handlers for the tools used in the code review flow.
    """

    @staticmethod
    async def handle_related_code_searcher(tool_input: Dict[str, Any]) -> Dict[str, Any]:
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
            "session_type": "PR_REVIEW"
        }
        payload = RelevantChunksParams(**payload)
        one_dev_review_client = OneDevReviewClient()
        embedding_manager = PRReviewEmbeddingManager(one_dev_client=one_dev_review_client)
        with ProcessPoolExecutor(
                max_workers=ConfigManager.configs["NUMBER_OF_WORKERS"]
        ) as executor:
            initialisation_manager = ReviewInitialisationManager(
                repo_path=payload.repo_path,
                process_executor=executor,
                one_dev_client=one_dev_review_client

            )

            chunks = await RelevantChunksService(
                payload.repo_path
            ).get_relevant_chunks(payload, one_dev_review_client, embedding_manager, initialisation_manager, executor)
        return chunks


    @staticmethod
    async def handle_grep_search(tool_input: Dict[str, Any]) -> Dict[str, Any]:
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
        grep_search_results = await GrepSearchService(
            repo_path=payload.repo_path
        ).perform_grep_search(
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
    async def handle_iterative_file_reader(tool_input: Dict[str, Any]) -> Dict[str, Any]:
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
    async  def handle_focused_snippets_searcher(tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle the focused_snippets_searcher tool request.
        
        Args:
            tool_input: The input for the tool.
            session_id: The session ID.
            
        Returns:
            The tool response.
        """
        tool_input["repo_path"] = get_context_value("repo_path")
        payload = BatchSearchParams(**tool_input)
        weaviate_client = await weaviate_connection()
        one_dev_client = OneDevReviewClient()
        with ProcessPoolExecutor(
                max_workers=ConfigManager.configs["NUMBER_OF_WORKERS"]
        ) as executor:
            initialisation_manager = ReviewInitialisationManager(
                repo_path=payload.repo_path,
                process_executor=executor,
                one_dev_client=one_dev_client

            )
            chunks = await BatchSearchService.search_code(payload, weaviate_client, initialisation_manager)
        return chunks


    @staticmethod
    async def handle_file_path_searcher(tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle the file_path_searcher tool request.
        
        Args:
            tool_input: The input for the tool.
            
        Returns:
            The tool response.
        """
        tool_input["repo_path"] = get_context_value("repo_path")
        payload = FilePathSearchPayload(**tool_input)
        files = FilePathSearchService(repo_path=payload.repo_path).list_files(
            directory=payload.directory,
            search_terms=payload.search_terms,
        )
        response = {
            "data": files,
        }
        return response

    @staticmethod
    async def handle_parse_final_response(tool_input: Dict[str, Any]) -> Dict[str, Any]:
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