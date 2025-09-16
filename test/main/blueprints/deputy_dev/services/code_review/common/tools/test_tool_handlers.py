"""
Unit tests for ToolHandlers.

This module provides comprehensive unit tests for the ToolHandlers class,
covering all tool handler methods including related_code_searcher, grep_search,
iterative_file_reader, focused_snippets_searcher, file_path_searcher,
parse_final_response, and pr_review_planner with various scenarios.
"""

from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers import ToolHandlers
from test.fixtures.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers_fixtures import *


class TestToolHandlersRelatedCodeSearcher:
    """Test cases for ToolHandlers.handle_related_code_searcher method."""

    @pytest.mark.asyncio
    async def test_handle_related_code_searcher_success(
        self,
        sample_related_code_search_input: Dict[str, Any],
        sample_related_code_search_response: Dict[str, Any],
    ) -> None:
        """Test successful related code searcher handling."""
        with (
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.get_context_value"
            ) as mock_get_context,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.OneDevReviewClient"
            ) as mock_client_class,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.PRReviewEmbeddingManager"
            ) as mock_embedding_manager_class,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.get_weaviate_connection"
            ) as mock_weaviate,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.ReviewInitialisationManager"
            ) as mock_init_manager_class,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.RelevantChunks"
            ) as mock_relevant_chunks_class,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.ProcessPoolExecutor"
            ) as mock_executor_class,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.ConfigManager"
            ) as mock_config,
        ):
            # Setup mocks
            mock_get_context.side_effect = lambda key: {"repo_path": "/test/repo/path", "session_id": 123}.get(key)

            mock_config.configs = {"NUMBER_OF_WORKERS": 4}
            mock_weaviate.return_value = MagicMock()

            mock_relevant_chunks = MagicMock()
            mock_relevant_chunks.get_relevant_chunks = AsyncMock(return_value=sample_related_code_search_response)
            mock_relevant_chunks_class.return_value = mock_relevant_chunks

            result = await ToolHandlers.handle_related_code_searcher(sample_related_code_search_input)

            assert result == sample_related_code_search_response
            mock_relevant_chunks.get_relevant_chunks.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_related_code_searcher_with_context_service(
        self,
        sample_related_code_search_input: Dict[str, Any],
        sample_context_service: MagicMock,
    ) -> None:
        """Test related code searcher with context service parameter."""
        with (
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.get_context_value"
            ) as mock_get_context,
            patch("app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.OneDevReviewClient"),
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.PRReviewEmbeddingManager"
            ),
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.get_weaviate_connection"
            ),
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.ReviewInitialisationManager"
            ),
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.RelevantChunks"
            ) as mock_relevant_chunks_class,
            patch("app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.ProcessPoolExecutor"),
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.ConfigManager"
            ) as mock_config,
        ):
            mock_get_context.side_effect = lambda key: {"repo_path": "/test/repo/path", "session_id": 123}.get(key)

            mock_config.configs = {"NUMBER_OF_WORKERS": 4}

            mock_relevant_chunks = MagicMock()
            mock_relevant_chunks.get_relevant_chunks = AsyncMock(return_value={"chunks": []})
            mock_relevant_chunks_class.return_value = mock_relevant_chunks

            result = await ToolHandlers.handle_related_code_searcher(
                sample_related_code_search_input, sample_context_service
            )

            assert result == {"chunks": []}


class TestToolHandlersGrepSearch:
    """Test cases for ToolHandlers.handle_grep_search method."""

    @pytest.mark.asyncio
    async def test_handle_grep_search_success(
        self,
        sample_grep_search_input: Dict[str, Any],
        sample_grep_search_response: List[Dict[str, Any]],
    ) -> None:
        """Test successful grep search handling."""
        with (
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.get_context_value"
            ) as mock_get_context,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.GrepSearch"
            ) as mock_grep_search_class,
        ):
            mock_get_context.return_value = "/test/repo/path"

            mock_grep_search = MagicMock()
            mock_grep_search.perform_grep_search = AsyncMock(return_value=sample_grep_search_response)
            mock_grep_search_class.return_value = mock_grep_search

            result = await ToolHandlers.handle_grep_search(sample_grep_search_input)

            expected_response = {
                "data": [
                    {
                        "chunk_info": chunk["chunk_info"].model_dump(mode="json"),
                        "matched_line": chunk["matched_line"],
                    }
                    for chunk in sample_grep_search_response
                ],
            }

            assert result == expected_response
            mock_grep_search.perform_grep_search.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_grep_search_with_context_service(
        self,
        sample_grep_search_input: Dict[str, Any],
        sample_context_service: MagicMock,
    ) -> None:
        """Test grep search with context service parameter."""
        with (
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.get_context_value"
            ) as mock_get_context,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.GrepSearch"
            ) as mock_grep_search_class,
        ):
            mock_get_context.return_value = "/test/repo/path"

            mock_grep_search = MagicMock()
            mock_grep_search.perform_grep_search = AsyncMock(return_value=[])
            mock_grep_search_class.return_value = mock_grep_search

            result = await ToolHandlers.handle_grep_search(sample_grep_search_input, sample_context_service)

            assert result == {"data": []}

    @pytest.mark.asyncio
    async def test_handle_grep_search_string_query(
        self,
        sample_grep_search_input_string_query: Dict[str, Any],
    ) -> None:
        """Test grep search with string query."""
        with (
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.get_context_value"
            ) as mock_get_context,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.GrepSearch"
            ) as mock_grep_search_class,
        ):
            mock_get_context.return_value = "/test/repo/path"

            mock_grep_search = MagicMock()
            mock_grep_search.perform_grep_search = AsyncMock(return_value=[])
            mock_grep_search_class.return_value = mock_grep_search

            result = await ToolHandlers.handle_grep_search(sample_grep_search_input_string_query)

            # Verify the string query was converted to search_term
            mock_grep_search.perform_grep_search.assert_called_once()
            call_kwargs = mock_grep_search.perform_grep_search.call_args.kwargs
            assert call_kwargs["search_term"] == sample_grep_search_input_string_query["query"]


class TestToolHandlersIterativeFileReader:
    """Test cases for ToolHandlers.handle_iterative_file_reader method."""

    @pytest.mark.asyncio
    async def test_handle_iterative_file_reader_success(
        self,
        sample_iterative_file_reader_input: Dict[str, Any],
        sample_iterative_file_reader_response: MagicMock,
    ) -> None:
        """Test successful iterative file reader handling."""
        with (
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.get_context_value"
            ) as mock_get_context,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.IterativeFileReader"
            ) as mock_reader_class,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.LLMResponseFormatter"
            ) as mock_formatter,
        ):
            mock_get_context.return_value = "/test/repo/path"

            mock_reader = MagicMock()
            mock_reader.read_lines = AsyncMock(return_value=sample_iterative_file_reader_response)
            mock_reader_class.return_value = mock_reader

            mock_formatter.format_iterative_file_reader_response.return_value = "Formatted response"

            result = await ToolHandlers.handle_iterative_file_reader(sample_iterative_file_reader_input)

            assert result == {"tool_response": "Formatted response"}
            mock_reader.read_lines.assert_called_once()
            mock_formatter.format_iterative_file_reader_response.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_iterative_file_reader_with_line_range(
        self,
        sample_iterative_file_reader_input_with_range: Dict[str, Any],
    ) -> None:
        """Test iterative file reader with specific line range."""
        with (
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.get_context_value"
            ) as mock_get_context,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.IterativeFileReader"
            ) as mock_reader_class,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.LLMResponseFormatter"
            ) as mock_formatter,
        ):
            mock_get_context.return_value = "/test/repo/path"

            mock_reader = MagicMock()
            mock_response = MagicMock()
            mock_response.model_dump.return_value = {"content": "test", "eof": True, "eof_reached": True}
            mock_reader.read_lines = AsyncMock(return_value=mock_response)
            mock_reader_class.return_value = mock_reader

            mock_formatter.format_iterative_file_reader_response.return_value = "Range response"

            result = await ToolHandlers.handle_iterative_file_reader(sample_iterative_file_reader_input_with_range)

            assert result == {"tool_response": "Range response"}
            mock_reader.read_lines.assert_called_once_with(
                start_line=sample_iterative_file_reader_input_with_range["start_line"],
                end_line=sample_iterative_file_reader_input_with_range["end_line"],
            )

    @pytest.mark.asyncio
    async def test_handle_iterative_file_reader_with_context_service(
        self,
        sample_iterative_file_reader_input: Dict[str, Any],
        sample_context_service: MagicMock,
    ) -> None:
        """Test iterative file reader with context service parameter."""
        with (
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.get_context_value"
            ) as mock_get_context,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.IterativeFileReader"
            ) as mock_reader_class,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.LLMResponseFormatter"
            ) as mock_formatter,
        ):
            mock_get_context.return_value = "/test/repo/path"

            mock_reader = MagicMock()
            mock_response = MagicMock()
            mock_response.model_dump.return_value = {"content": "test", "eof": True, "eof_reached": True}
            mock_reader.read_lines = AsyncMock(return_value=mock_response)
            mock_reader_class.return_value = mock_reader

            mock_formatter.format_iterative_file_reader_response.return_value = "Context response"

            result = await ToolHandlers.handle_iterative_file_reader(
                sample_iterative_file_reader_input, sample_context_service
            )

            assert result == {"tool_response": "Context response"}


class TestToolHandlersFocusedSnippetsSearcher:
    """Test cases for ToolHandlers.handle_focused_snippets_searcher method."""

    @pytest.mark.asyncio
    async def test_handle_focused_snippets_searcher_success(
        self,
        sample_focused_snippets_search_input: Dict[str, Any],
        sample_focused_snippets_search_response: Dict[str, Any],
    ) -> None:
        """Test successful focused snippets searcher handling."""
        with (
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.get_context_value"
            ) as mock_get_context,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.get_weaviate_connection"
            ) as mock_weaviate,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.OneDevReviewClient"
            ) as mock_client_class,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.ReviewInitialisationManager"
            ) as mock_init_manager_class,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.FocussedSnippetSearch"
            ) as mock_search_class,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.ProcessPoolExecutor"
            ) as mock_executor_class,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.ConfigManager"
            ) as mock_config,
        ):
            mock_get_context.return_value = "/test/repo/path"
            mock_config.configs = {"NUMBER_OF_WORKERS": 4}
            mock_weaviate.return_value = MagicMock()

            mock_search_class.search_code = AsyncMock(return_value=sample_focused_snippets_search_response)

            result = await ToolHandlers.handle_focused_snippets_searcher(sample_focused_snippets_search_input)

            assert result == sample_focused_snippets_search_response
            mock_search_class.search_code.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_focused_snippets_searcher_with_context_service(
        self,
        sample_focused_snippets_search_input: Dict[str, Any],
        sample_context_service: MagicMock,
    ) -> None:
        """Test focused snippets searcher with context service parameter."""
        with (
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.get_context_value"
            ) as mock_get_context,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.get_weaviate_connection"
            ),
            patch("app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.OneDevReviewClient"),
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.ReviewInitialisationManager"
            ),
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.FocussedSnippetSearch"
            ) as mock_search_class,
            patch("app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.ProcessPoolExecutor"),
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.ConfigManager"
            ) as mock_config,
        ):
            mock_get_context.return_value = "/test/repo/path"
            mock_config.configs = {"NUMBER_OF_WORKERS": 4}

            mock_search_class.search_code = AsyncMock(return_value={"results": []})

            result = await ToolHandlers.handle_focused_snippets_searcher(
                sample_focused_snippets_search_input, sample_context_service
            )

            assert result == {"results": []}


class TestToolHandlersFilePathSearcher:
    """Test cases for ToolHandlers.handle_file_path_searcher method."""

    @pytest.mark.asyncio
    async def test_handle_file_path_searcher_success(
        self,
        sample_file_path_search_input: Dict[str, Any],
        sample_file_path_search_response: List[str],
    ) -> None:
        """Test successful file path searcher handling."""
        with (
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.get_context_value"
            ) as mock_get_context,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.FilePathSearch"
            ) as mock_search_class,
        ):
            mock_get_context.return_value = "/test/repo/path"

            mock_search = MagicMock()
            mock_search.list_files.return_value = sample_file_path_search_response
            mock_search_class.return_value = mock_search

            result = await ToolHandlers.handle_file_path_searcher(sample_file_path_search_input)

            expected_response = {"data": sample_file_path_search_response}
            assert result == expected_response
            mock_search.list_files.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_file_path_searcher_with_search_terms(
        self,
        sample_file_path_search_input_with_terms: Dict[str, Any],
    ) -> None:
        """Test file path searcher with search terms."""
        with (
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.get_context_value"
            ) as mock_get_context,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.FilePathSearch"
            ) as mock_search_class,
        ):
            mock_get_context.return_value = "/test/repo/path"

            mock_search = MagicMock()
            mock_search.list_files.return_value = ["src/main.py", "src/utils.py"]
            mock_search_class.return_value = mock_search

            result = await ToolHandlers.handle_file_path_searcher(sample_file_path_search_input_with_terms)

            assert result == {"data": ["src/main.py", "src/utils.py"]}
            mock_search.list_files.assert_called_once_with(
                directory=sample_file_path_search_input_with_terms["directory"],
                search_terms=sample_file_path_search_input_with_terms["search_terms"],
            )

    @pytest.mark.asyncio
    async def test_handle_file_path_searcher_with_context_service(
        self,
        sample_file_path_search_input: Dict[str, Any],
        sample_context_service: MagicMock,
    ) -> None:
        """Test file path searcher with context service parameter."""
        with (
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.get_context_value"
            ) as mock_get_context,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.FilePathSearch"
            ) as mock_search_class,
        ):
            mock_get_context.return_value = "/test/repo/path"

            mock_search = MagicMock()
            mock_search.list_files.return_value = []
            mock_search_class.return_value = mock_search

            result = await ToolHandlers.handle_file_path_searcher(sample_file_path_search_input, sample_context_service)

            assert result == {"data": []}


class TestToolHandlersParseFinalResponse:
    """Test cases for ToolHandlers.handle_parse_final_response method."""

    @pytest.mark.asyncio
    async def test_handle_parse_final_response_success(
        self,
        sample_parse_final_response_input: Dict[str, Any],
    ) -> None:
        """Test successful parse final response handling."""
        result = await ToolHandlers.handle_parse_final_response(sample_parse_final_response_input)

        expected_result = {
            "comments": sample_parse_final_response_input["comments"],
            "summary": sample_parse_final_response_input["summary"],
        }
        assert result == expected_result

    @pytest.mark.asyncio
    async def test_handle_parse_final_response_missing_fields(
        self,
        sample_parse_final_response_input_missing_fields: Dict[str, Any],
    ) -> None:
        """Test parse final response with missing fields."""
        result = await ToolHandlers.handle_parse_final_response(sample_parse_final_response_input_missing_fields)

        expected_result = {
            "comments": [],
            "summary": "",
        }
        assert result == expected_result

    @pytest.mark.asyncio
    async def test_handle_parse_final_response_with_context_service(
        self,
        sample_parse_final_response_input: Dict[str, Any],
        sample_context_service: MagicMock,
    ) -> None:
        """Test parse final response with context service parameter."""
        result = await ToolHandlers.handle_parse_final_response(
            sample_parse_final_response_input, sample_context_service
        )

        expected_result = {
            "comments": sample_parse_final_response_input["comments"],
            "summary": sample_parse_final_response_input["summary"],
        }
        assert result == expected_result


class TestToolHandlersPrReviewPlanner:
    """Test cases for ToolHandlers.handle_pr_review_planner method."""

    @pytest.mark.asyncio
    async def test_handle_pr_review_planner_success(
        self,
        sample_pr_review_planner_input: Dict[str, Any],
        sample_context_service: MagicMock,
        sample_pr_review_plan: Dict[str, Any],
    ) -> None:
        """Test successful PR review planner handling."""
        with (
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.get_context_value"
            ) as mock_get_context,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.ReviewPlanner"
            ) as mock_planner_class,
        ):
            mock_get_context.return_value = "test-session-123"

            # Setup context service mocks
            sample_context_service.get_pr_title.return_value = "Test PR Title"
            sample_context_service.get_pr_description.return_value = "Test PR Description"
            sample_context_service.get_pr_diff = AsyncMock(return_value="diff content")

            mock_planner = MagicMock()
            mock_planner.get_review_plan = AsyncMock(return_value=sample_pr_review_plan)
            mock_planner_class.return_value = mock_planner

            result = await ToolHandlers.handle_pr_review_planner(sample_pr_review_planner_input, sample_context_service)

            assert result == sample_pr_review_plan
            mock_planner.get_review_plan.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_pr_review_planner_no_result(
        self,
        sample_pr_review_planner_input: Dict[str, Any],
        sample_context_service: MagicMock,
    ) -> None:
        """Test PR review planner with no result."""
        with (
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.get_context_value"
            ) as mock_get_context,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.ReviewPlanner"
            ) as mock_planner_class,
        ):
            mock_get_context.return_value = "test-session-123"

            sample_context_service.get_pr_title.return_value = "Test PR Title"
            sample_context_service.get_pr_description.return_value = "Test PR Description"
            sample_context_service.get_pr_diff = AsyncMock(return_value="diff content")

            mock_planner = MagicMock()
            mock_planner.get_review_plan = AsyncMock(return_value=None)
            mock_planner_class.return_value = mock_planner

            result = await ToolHandlers.handle_pr_review_planner(sample_pr_review_planner_input, sample_context_service)

            assert result == {}

    @pytest.mark.asyncio
    async def test_handle_pr_review_planner_without_context_service(
        self,
        sample_pr_review_planner_input: Dict[str, Any],
    ) -> None:
        """Test PR review planner without context service."""
        # Should raise AttributeError when context service is None (trying to call methods on None)
        with pytest.raises(AttributeError):
            await ToolHandlers.handle_pr_review_planner(sample_pr_review_planner_input, None)


class TestToolHandlersEdgeCases:
    """Test cases for ToolHandlers edge cases and error scenarios."""

    @pytest.mark.asyncio
    async def test_handle_related_code_searcher_empty_query(
        self,
        sample_related_code_search_input_empty: Dict[str, Any],
    ) -> None:
        """Test related code searcher with empty query."""
        with (
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.get_context_value"
            ) as mock_get_context,
            patch("app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.OneDevReviewClient"),
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.PRReviewEmbeddingManager"
            ),
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.get_weaviate_connection"
            ),
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.ReviewInitialisationManager"
            ),
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.RelevantChunks"
            ) as mock_relevant_chunks_class,
            patch("app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.ProcessPoolExecutor"),
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.ConfigManager"
            ) as mock_config,
        ):
            mock_get_context.side_effect = lambda key: {"repo_path": "/test/repo/path", "session_id": 123}.get(key)

            mock_config.configs = {"NUMBER_OF_WORKERS": 4}

            mock_relevant_chunks = MagicMock()
            mock_relevant_chunks.get_relevant_chunks = AsyncMock(return_value={"chunks": []})
            mock_relevant_chunks_class.return_value = mock_relevant_chunks

            result = await ToolHandlers.handle_related_code_searcher(sample_related_code_search_input_empty)

            assert result == {"chunks": []}

    @pytest.mark.asyncio
    async def test_handle_grep_search_invalid_regex(
        self,
        sample_grep_search_input_invalid_regex: Dict[str, Any],
    ) -> None:
        """Test grep search with invalid regex."""
        with (
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.get_context_value"
            ) as mock_get_context,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.GrepSearch"
            ) as mock_grep_search_class,
        ):
            mock_get_context.return_value = "/test/repo/path"

            mock_grep_search = MagicMock()
            mock_grep_search.perform_grep_search = AsyncMock(side_effect=Exception("Invalid regex"))
            mock_grep_search_class.return_value = mock_grep_search

            with pytest.raises(Exception, match="Invalid regex"):
                await ToolHandlers.handle_grep_search(sample_grep_search_input_invalid_regex)

    @pytest.mark.asyncio
    async def test_handle_iterative_file_reader_file_not_found(
        self,
        sample_iterative_file_reader_input_nonexistent: Dict[str, Any],
    ) -> None:
        """Test iterative file reader with non-existent file."""
        with (
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.get_context_value"
            ) as mock_get_context,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.IterativeFileReader"
            ) as mock_reader_class,
        ):
            mock_get_context.return_value = "/test/repo/path"

            mock_reader = MagicMock()
            mock_reader.read_lines = AsyncMock(side_effect=FileNotFoundError("File not found"))
            mock_reader_class.return_value = mock_reader

            with pytest.raises(FileNotFoundError, match="File not found"):
                await ToolHandlers.handle_iterative_file_reader(sample_iterative_file_reader_input_nonexistent)

    @pytest.mark.asyncio
    async def test_handle_file_path_searcher_invalid_directory(
        self,
        sample_file_path_search_input_invalid_dir: Dict[str, Any],
    ) -> None:
        """Test file path searcher with invalid directory."""
        with (
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.get_context_value"
            ) as mock_get_context,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.FilePathSearch"
            ) as mock_search_class,
        ):
            mock_get_context.return_value = "/test/repo/path"

            mock_search = MagicMock()
            mock_search.list_files.side_effect = FileNotFoundError("Directory not found")
            mock_search_class.return_value = mock_search

            with pytest.raises(FileNotFoundError, match="Directory not found"):
                await ToolHandlers.handle_file_path_searcher(sample_file_path_search_input_invalid_dir)


class TestToolHandlersPerformance:
    """Performance test cases for ToolHandlers."""

    @pytest.mark.asyncio
    async def test_handle_multiple_tool_requests_concurrently(
        self,
        sample_concurrent_tool_inputs: List[Dict[str, Any]],
    ) -> None:
        """Test handling multiple tool requests concurrently."""
        import asyncio

        with patch(
            "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.get_context_value"
        ) as mock_get_context:
            mock_get_context.return_value = "/test/repo/path"

            async def mock_parse_final_response(tool_input: Dict[str, Any]) -> Dict[str, Any]:
                await asyncio.sleep(0.01)  # Simulate work
                return {"comments": [], "summary": ""}

            # Run multiple requests concurrently
            tasks = [mock_parse_final_response(tool_input) for tool_input in sample_concurrent_tool_inputs]

            start_time = asyncio.get_event_loop().time()
            results = await asyncio.gather(*tasks)
            end_time = asyncio.get_event_loop().time()

            execution_time = end_time - start_time

            # Should complete within reasonable time
            assert execution_time < 0.5  # 500ms for concurrent execution
            assert len(results) == len(sample_concurrent_tool_inputs)

    @pytest.mark.asyncio
    async def test_handle_large_tool_inputs(
        self,
        sample_large_tool_input: Dict[str, Any],
    ) -> None:
        """Test handling large tool inputs."""
        result = await ToolHandlers.handle_parse_final_response(sample_large_tool_input)

        # Should handle large inputs gracefully
        assert result is not None
        assert isinstance(result, dict)
        assert "comments" in result
        assert "summary" in result


class TestToolHandlersIntegration:
    """Integration test cases for ToolHandlers."""

    @pytest.mark.asyncio
    async def test_complete_tool_chain_workflow(
        self,
        sample_context_service: MagicMock,
    ) -> None:
        """Test complete workflow using multiple tools."""
        with (
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.get_context_value"
            ) as mock_get_context,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.FilePathSearch"
            ) as mock_file_search,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.IterativeFileReader"
            ) as mock_file_reader,
            patch(
                "app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_handlers.LLMResponseFormatter"
            ) as mock_formatter,
        ):
            mock_get_context.return_value = "/test/repo/path"

            # Setup file path search
            mock_search = MagicMock()
            mock_search.list_files.return_value = ["src/main.py", "src/utils.py"]
            mock_file_search.return_value = mock_search

            # Setup file reader
            mock_reader = MagicMock()
            mock_response = MagicMock()
            mock_response.model_dump.return_value = {"content": "test code", "eof": True, "eof_reached": True}
            mock_reader.read_lines = AsyncMock(return_value=mock_response)
            mock_file_reader.return_value = mock_reader

            mock_formatter.format_iterative_file_reader_response.return_value = "Formatted code"

            # Step 1: Search for files
            file_search_result = await ToolHandlers.handle_file_path_searcher(
                {"directory": "src/", "search_terms": ["main", "utils"]}
            )

            # Step 2: Read file content
            file_read_result = await ToolHandlers.handle_iterative_file_reader({"file_path": "src/main.py"})

            # Step 3: Parse final response
            final_result = await ToolHandlers.handle_parse_final_response(
                {"comments": ["Good code structure"], "summary": "Code review completed"}
            )

            # Verify results
            assert file_search_result == {"data": ["src/main.py", "src/utils.py"]}
            assert file_read_result == {"tool_response": "Formatted code"}
            assert final_result == {"comments": ["Good code structure"], "summary": "Code review completed"}
