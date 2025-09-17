"""
Fixtures for testing LLMBasedChunkReranker.

This module provides comprehensive fixtures for testing various scenarios
of the LLMBasedChunkReranker methods.
"""

from typing import List
from unittest.mock import AsyncMock, MagicMock

import pytest


# Create mock ChunkInfo class since deputydev_core is external
class MockChunkInfo:
    """Mock ChunkInfo for testing purposes."""

    def __init__(self, denotation: str, content: str = "", file_path: str = "", line_number: int = 1):
        self.denotation = denotation
        self.content = content
        self.file_path = file_path
        self.line_number = line_number

    def __eq__(self, other):
        if not isinstance(other, MockChunkInfo):
            return False
        return self.denotation == other.denotation


@pytest.fixture
def mock_chunk_info_class():
    """Provide the MockChunkInfo class for use in tests."""
    return MockChunkInfo


@pytest.fixture
def sample_focus_chunks() -> List[MockChunkInfo]:
    """Sample focus chunks for testing."""
    return [
        MockChunkInfo(
            denotation="focus_1",
            content="def calculate_sum(a, b):\n    return a + b",
            file_path="src/calculator.py",
            line_number=10,
        ),
        MockChunkInfo(
            denotation="focus_2",
            content="class Calculator:\n    def __init__(self):\n        pass",
            file_path="src/calculator.py",
            line_number=1,
        ),
    ]


@pytest.fixture
def sample_related_chunks() -> List[MockChunkInfo]:
    """Sample related codebase chunks for testing."""
    return [
        MockChunkInfo(
            denotation="related_1",
            content="def multiply(x, y):\n    return x * y",
            file_path="src/math_utils.py",
            line_number=5,
        ),
        MockChunkInfo(
            denotation="related_2",
            content="def divide(x, y):\n    if y == 0:\n        raise ValueError('Division by zero')\n    return x / y",
            file_path="src/math_utils.py",
            line_number=15,
        ),
        MockChunkInfo(
            denotation="related_3",
            content="# Helper function for logging\ndef log_operation(op, result):\n    print(f'{op} result: {result}')",
            file_path="src/logger.py",
            line_number=1,
        ),
    ]


@pytest.fixture
def empty_chunks() -> List[MockChunkInfo]:
    """Empty list of chunks for testing edge cases."""
    return []


@pytest.fixture
def single_chunk() -> List[MockChunkInfo]:
    """Single chunk for testing edge cases."""
    return [
        MockChunkInfo(
            denotation="single_chunk",
            content="def hello_world():\n    print('Hello, World!')",
            file_path="src/hello.py",
            line_number=1,
        )
    ]


@pytest.fixture
def large_chunk_list() -> List[MockChunkInfo]:
    """Large list of chunks for performance testing."""
    chunks = []
    for i in range(50):
        chunks.append(
            MockChunkInfo(
                denotation=f"chunk_{i}",
                content=f"def function_{i}():\n    return {i}",
                file_path=f"src/module_{i // 10}.py",
                line_number=(i % 10) + 1,
            )
        )
    return chunks


@pytest.fixture
def sample_query() -> str:
    """Sample query string for reranking."""
    return "Find functions that perform mathematical calculations"


@pytest.fixture
def complex_query() -> str:
    """Complex query for testing advanced scenarios."""
    return "How do I implement error handling for mathematical operations in Python?"


@pytest.fixture
def empty_query() -> str:
    """Empty query for edge case testing."""
    return ""


@pytest.fixture
def very_long_query() -> str:
    """Very long query for testing performance."""
    return "This is a very long query " * 50 + " that tests how the reranker handles large input strings."


@pytest.fixture
def mock_llm_handler():
    """Mock LLMHandler for testing."""
    handler = MagicMock()
    handler.start_llm_query = AsyncMock()
    return handler


@pytest.fixture
def successful_llm_response():
    """Mock successful LLM response."""
    from deputydev_core.llm_handler.dataclasses.main import NonStreamingParsedLLMCallResponse

    response = MagicMock(spec=NonStreamingParsedLLMCallResponse)
    response.parsed_content = [{"chunks_source": ["focus_1", "related_2", "related_1"]}]
    return response


@pytest.fixture
def successful_llm_response_partial():
    """Mock LLM response with partial chunk matches."""
    from deputydev_core.llm_handler.dataclasses.main import NonStreamingParsedLLMCallResponse

    response = MagicMock(spec=NonStreamingParsedLLMCallResponse)
    response.parsed_content = [{"chunks_source": ["focus_1", "non_existent_chunk", "related_1"]}]
    return response


@pytest.fixture
def successful_llm_response_empty_chunks():
    """Mock LLM response with empty chunks list."""
    from deputydev_core.llm_handler.dataclasses.main import NonStreamingParsedLLMCallResponse

    response = MagicMock(spec=NonStreamingParsedLLMCallResponse)
    response.parsed_content = [{"chunks_source": []}]
    return response


@pytest.fixture
def malformed_llm_response_missing_key():
    """Mock malformed LLM response missing chunks_source key."""
    from deputydev_core.llm_handler.dataclasses.main import NonStreamingParsedLLMCallResponse

    response = MagicMock(spec=NonStreamingParsedLLMCallResponse)
    response.parsed_content = [{"invalid_key": ["focus_1", "related_1"]}]
    return response


@pytest.fixture
def malformed_llm_response_wrong_type():
    """Mock malformed LLM response with wrong type."""
    from deputydev_core.llm_handler.dataclasses.main import NonStreamingParsedLLMCallResponse

    response = MagicMock(spec=NonStreamingParsedLLMCallResponse)
    response.parsed_content = [
        {
            "chunks_source": "focus_1,related_1"  # String instead of list
        }
    ]
    return response


@pytest.fixture
def malformed_llm_response_empty_list():
    """Mock malformed LLM response with empty parsed_content."""
    from deputydev_core.llm_handler.dataclasses.main import NonStreamingParsedLLMCallResponse

    response = MagicMock(spec=NonStreamingParsedLLMCallResponse)
    response.parsed_content = []
    return response


@pytest.fixture
def malformed_llm_response_none():
    """Mock malformed LLM response with None parsed_content."""
    from deputydev_core.llm_handler.dataclasses.main import NonStreamingParsedLLMCallResponse

    response = MagicMock(spec=NonStreamingParsedLLMCallResponse)
    response.parsed_content = None
    return response


@pytest.fixture
def none_llm_response():
    """Mock None LLM response."""
    return None


@pytest.fixture
def denotation_list_basic() -> List[str]:
    """Basic list of denotations for testing get_chunks_from_denotation."""
    return ["focus_1", "related_2"]


@pytest.fixture
def denotation_list_empty() -> List[str]:
    """Empty list of denotations."""
    return []


@pytest.fixture
def denotation_list_non_existent() -> List[str]:
    """List of non-existent denotations."""
    return ["non_existent_1", "non_existent_2"]


@pytest.fixture
def denotation_list_mixed() -> List[str]:
    """Mixed list with existing and non-existent denotations."""
    return ["focus_1", "non_existent", "related_1", "another_non_existent"]


@pytest.fixture
def mock_render_snippet_array():
    """Mock render_snippet_array function."""

    def mock_render(chunks):
        return f"Rendered {len(chunks)} chunks"

    return mock_render


@pytest.fixture
def session_id() -> int:
    """Sample session ID for testing."""
    return 12345


@pytest.fixture
def different_session_id() -> int:
    """Different session ID for testing."""
    return 67890


@pytest.fixture
def mock_app_logger():
    """Mock AppLogger for testing."""
    logger = MagicMock()
    logger.log_info = MagicMock()
    logger.log_warn = MagicMock()
    logger.log_error = MagicMock()
    return logger


@pytest.fixture
def mock_asyncio_sleep():
    """Mock asyncio.sleep for testing retry logic."""
    return AsyncMock()


@pytest.fixture
def mock_time_perf_counter():
    """Mock time.perf_counter for testing performance logging."""
    counter = MagicMock()
    counter.side_effect = [0.0, 1.5]  # Start and end times
    return counter


@pytest.fixture
def llm_based_chunk_reranker():
    """Create a fresh LLMBasedChunkReranker instance for each test."""
    from app.backend_common.services.chunking.rerankers.handler.llm_based.reranker import LLMBasedChunkReranker

    return LLMBasedChunkReranker(session_id=12345)


@pytest.fixture
def combined_chunks_basic(sample_focus_chunks, sample_related_chunks) -> List[MockChunkInfo]:
    """Combined focus and related chunks for testing."""
    return sample_focus_chunks + sample_related_chunks


@pytest.fixture
def combined_chunks_large(sample_focus_chunks, sample_related_chunks, large_chunk_list) -> List[MockChunkInfo]:
    """Large combined chunks list for performance testing."""
    return sample_focus_chunks + sample_related_chunks + large_chunk_list
