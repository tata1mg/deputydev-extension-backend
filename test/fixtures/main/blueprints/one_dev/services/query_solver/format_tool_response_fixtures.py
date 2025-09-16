"""
Fixtures for testing QuerySolver._format_tool_response method.

This module provides comprehensive fixtures for testing various scenarios
of the _format_tool_response method including different tool types,
response structures, and edge cases.
"""

from typing import List
from unittest.mock import MagicMock, patch

import pytest

from app.main.blueprints.one_dev.constants.tools import ToolStatus
from app.main.blueprints.one_dev.services.query_solver.dataclasses.main import (
    ClassFocusItem,
    DirectoryEntry,
    DirectoryFocusItem,
    FileFocusItem,
    FocusItem,
    FocusItemTypes,
    ToolUseResponseInput,
    UrlFocusItem,
)


@pytest.fixture
def mock_chunk_info() -> MagicMock:
    """Create a mock ChunkInfo instance."""
    with patch("deputydev_core.services.chunking.chunk_info.ChunkInfo") as mock:
        instance = MagicMock()
        instance.get_xml.return_value = "<chunk>test chunk content</chunk>"
        mock.return_value = instance
        return mock


@pytest.fixture
def mock_llm_response_formatter() -> MagicMock:
    """Create a mock LLMResponseFormatter."""
    with patch("app.backend_common.utils.tool_response_parser.LLMResponseFormatter") as mock:
        mock.format_iterative_file_reader_response.return_value = (
            "### File: `/test/file.py`\n- Lines: 1-10\n- Content: test content"
        )
        mock.format_grep_tool_response.return_value = "### Grep Results\nFound 2 matches in test.py"
        mock.format_ask_user_input_response.return_value = {
            "user_response": "Yes, proceed",
            "focus_items": "Focus on test.py",
            "vscode_env": "development",
        }
        return mock


@pytest.fixture
def completed_tool_response() -> ToolUseResponseInput:
    """Create a basic completed tool response."""
    return ToolUseResponseInput(
        tool_name="test_tool",
        tool_use_id="test-tool-id",
        response={"result": "success", "data": "test data"},
        status=ToolStatus.COMPLETED,
    )


@pytest.fixture
def failed_tool_response() -> ToolUseResponseInput:
    """Create a failed tool response."""
    return ToolUseResponseInput(
        tool_name="failing_tool",
        tool_use_id="failed-tool-id",
        response={"error": "Tool execution failed", "code": 500},
        status=ToolStatus.FAILED,
    )


@pytest.fixture
def empty_response_tool() -> ToolUseResponseInput:
    """Create a tool response with empty response."""
    return ToolUseResponseInput(
        tool_name="empty_tool",
        tool_use_id="empty-tool-id",
        response={},
        status=ToolStatus.COMPLETED,
    )


@pytest.fixture
def focused_snippets_tool_response() -> ToolUseResponseInput:
    """Create a focused_snippets_searcher tool response."""
    return ToolUseResponseInput(
        tool_name="focused_snippets_searcher",
        tool_use_id="snippets-tool-id",
        response={
            "batch_chunks_search": {
                "response": [
                    {
                        "chunks": [
                            {
                                "chunk_id": "chunk1",
                                "content": "def test_function():\n    return True",
                                "source_details": {
                                    "file_path": "/test/file.py",
                                    "start_line": 1,
                                    "end_line": 2,
                                },
                            }
                        ]
                    },
                    {
                        "chunks": [
                            {
                                "chunk_id": "chunk2",
                                "content": "class TestClass:\n    pass",
                                "source_details": {
                                    "file_path": "/test/class.py",
                                    "start_line": 5,
                                    "end_line": 6,
                                },
                            }
                        ]
                    },
                ]
            }
        },
        status=ToolStatus.COMPLETED,
    )


@pytest.fixture
def iterative_file_reader_tool_response() -> ToolUseResponseInput:
    """Create an iterative_file_reader tool response."""
    return ToolUseResponseInput(
        tool_name="iterative_file_reader",
        tool_use_id="file-reader-tool-id",
        response={
            "data": {
                "chunk": {
                    "content": "import os\nimport sys\n\ndef main():\n    print('Hello World')",
                    "source_details": {
                        "file_path": "/test/main.py",
                        "start_line": 1,
                        "end_line": 5,
                    },
                },
                "eof_reached": True,
                "was_summary": False,
                "total_lines": 5,
            }
        },
        status=ToolStatus.COMPLETED,
    )


@pytest.fixture
def grep_search_tool_response() -> ToolUseResponseInput:
    """Create a grep_search tool response."""
    return ToolUseResponseInput(
        tool_name="grep_search",
        tool_use_id="grep-tool-id",
        response={
            "data": [
                {
                    "chunk_info": {
                        "content": "def test_function():\n    return True",
                        "source_details": {
                            "file_path": "/test/file.py",
                            "start_line": 1,
                            "end_line": 2,
                        },
                    },
                    "matched_lines": [1],
                }
            ],
            "search_term": "test_function",
            "directory_path": "/test",
            "case_insensitive": False,
            "use_regex": False,
        },
        status=ToolStatus.COMPLETED,
    )


@pytest.fixture
def ask_user_input_tool_response() -> ToolUseResponseInput:
    """Create an ask_user_input tool response."""
    return ToolUseResponseInput(
        tool_name="ask_user_input",
        tool_use_id="user-input-tool-id",
        response={
            "user_response": "Yes, please proceed with the changes",
            "timestamp": "2023-01-01T12:00:00Z",
        },
        status=ToolStatus.COMPLETED,
    )


@pytest.fixture
def unknown_tool_response() -> ToolUseResponseInput:
    """Create an unknown tool response."""
    return ToolUseResponseInput(
        tool_name="unknown_tool",
        tool_use_id="unknown-tool-id",
        response={
            "custom_data": "some custom response",
            "result": "success",
        },
        status=ToolStatus.COMPLETED,
    )


@pytest.fixture
def sample_vscode_env() -> str:
    """Create sample VSCode environment data."""
    return """
# VSCode Visible Files
- /test/main.py
- /test/utils.py

# VSCode Open Tabs
- /test/main.py (active)
- /test/utils.py
- /test/config.json

# Current Time
2023-01-01, 12:00:00 PM (UTC+0:00)
"""


@pytest.fixture
def sample_focus_items() -> List[FocusItem]:
    """Create sample focus items."""
    return [
        FileFocusItem(
            type=FocusItemTypes.FILE,
            path="/test/main.py",
            value="main.py",
        ),
        ClassFocusItem(
            type=FocusItemTypes.CLASS,
            path="/test/models.py",
            value="TestClass",
            chunks=[],
        ),
        DirectoryFocusItem(
            type=FocusItemTypes.DIRECTORY,
            path="/test/utils",
            value="utils",
            structure=[
                DirectoryEntry(name="helper.py", type="file"),
                DirectoryEntry(name="constants.py", type="file"),
            ],
        ),
        UrlFocusItem(
            type=FocusItemTypes.URL,
            value="API Documentation",
            url="https://api.example.com/docs",
        ),
    ]


@pytest.fixture
def empty_focus_items() -> List[FocusItem]:
    """Create empty focus items list."""
    return []


@pytest.fixture
def malformed_focused_snippets_response() -> ToolUseResponseInput:
    """Create a malformed focused_snippets_searcher response."""
    return ToolUseResponseInput(
        tool_name="focused_snippets_searcher",
        tool_use_id="malformed-snippets-id",
        response={
            "batch_chunks_search": {
                "response": [
                    {
                        "chunks": [
                            {
                                # Missing required fields to test error handling
                                "content": "incomplete chunk data",
                            }
                        ]
                    }
                ]
            }
        },
        status=ToolStatus.COMPLETED,
    )


@pytest.fixture
def large_focused_snippets_response() -> ToolUseResponseInput:
    """Create a large focused_snippets_searcher response with multiple chunks."""
    chunks = []
    for i in range(10):
        chunks.append(
            {
                "chunk_id": f"chunk{i}",
                "content": f"def function_{i}():\n    return {i}",
                "source_details": {
                    "file_path": f"/test/file_{i}.py",
                    "start_line": i * 10 + 1,
                    "end_line": i * 10 + 2,
                },
            }
        )

    return ToolUseResponseInput(
        tool_name="focused_snippets_searcher",
        tool_use_id="large-snippets-id",
        response={
            "batch_chunks_search": {
                "response": [
                    {"chunks": chunks[:5]},
                    {"chunks": chunks[5:]},
                ]
            }
        },
        status=ToolStatus.COMPLETED,
    )


@pytest.fixture
def complex_ask_user_input_response() -> ToolUseResponseInput:
    """Create a complex ask_user_input tool response with structured data."""
    return ToolUseResponseInput(
        tool_name="ask_user_input",
        tool_use_id="complex-user-input-id",
        response={
            "user_response": {"action": "approve", "modifications": ["add tests", "update docs"], "priority": "high"},
            "metadata": {"timestamp": "2023-01-01T12:00:00Z", "session_id": "test-session-123"},
        },
        status=ToolStatus.COMPLETED,
    )


@pytest.fixture
def partial_tool_response() -> ToolUseResponseInput:
    """Create a tool response with ABORTED status (using available status)."""
    return ToolUseResponseInput(
        tool_name="partial_tool",
        tool_use_id="partial-tool-id",
        response={"progress": 50, "partial_result": "halfway done"},
        status=ToolStatus.ABORTED,
    )


@pytest.fixture
def cancelled_tool_response() -> ToolUseResponseInput:
    """Create a tool response with ABORTED status (using available status)."""
    return ToolUseResponseInput(
        tool_name="cancelled_tool",
        tool_use_id="cancelled-tool-id",
        response={"reason": "User cancelled operation"},
        status=ToolStatus.ABORTED,
    )
