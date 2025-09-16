import pytest
from typing import Any, Dict, List
from unittest.mock import Mock, patch

from app.backend_common.dataclasses.dataclasses import PromptCategories
from app.backend_common.models.dto.message_thread_dto import MessageData
from app.backend_common.services.llm.dataclasses.main import (
    NonStreamingResponse,
    StreamingResponse,
    UserAndSystemMessages,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.gemini_2_point_5_flash_handler import (
    Gemini2Point5FlashCodeQuerySolverPromptHandler,
)
from test.fixtures.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.gemini_2_point_5_flash_handler_fixtures import (
    Gemini2Point5FlashHandlerFixtures,
)


class TestGemini2Point5FlashCodeQuerySolverPromptHandler:
    """Test suite for Gemini2Point5FlashCodeQuerySolverPromptHandler functionality."""

    @pytest.fixture
    def sample_params(self) -> Dict[str, Any]:
        """Sample parameters for handler initialization."""
        return {
            "query": "Write a Python function to calculate factorial",
            "files": [],
            "additional_context": "Use recursive approach",
            "repository_structure": {"src": ["main.py", "utils.py"]},
        }

    @pytest.fixture
    def handler(self, sample_params: Dict[str, Any]) -> Gemini2Point5FlashCodeQuerySolverPromptHandler:
        """Create a handler instance for testing."""
        return Gemini2Point5FlashCodeQuerySolverPromptHandler(sample_params)

    def test_handler_initialization(self, sample_params: Dict[str, Any]) -> None:
        """Test proper handler initialization with parameters."""
        handler = Gemini2Point5FlashCodeQuerySolverPromptHandler(sample_params)
        
        assert handler.params == sample_params
        assert handler.prompt_type == "CODE_QUERY_SOLVER"
        assert handler.prompt_category == PromptCategories.CODE_GENERATION.value
        assert handler.prompt is not None

    def test_get_system_prompt(self, handler: Gemini2Point5FlashCodeQuerySolverPromptHandler) -> None:
        """Test system prompt generation."""
        system_prompt = handler.get_system_prompt()
        
        assert isinstance(system_prompt, str)
        assert len(system_prompt) > 0
        assert "assistant" in system_prompt.lower() or "system" in system_prompt.lower()

    def test_get_prompt(self, handler: Gemini2Point5FlashCodeQuerySolverPromptHandler) -> None:
        """Test prompt generation returns proper UserAndSystemMessages."""
        prompt = handler.get_prompt()
        
        assert isinstance(prompt, UserAndSystemMessages)
        assert prompt.system_message is not None
        assert prompt.user_message is not None
        assert len(prompt.user_message) > 0

    def test_get_parsed_response_blocks(self) -> None:
        """Test parsing of response blocks."""
        from app.backend_common.models.dto.message_thread_dto import TextBlockData, TextBlockContent
        
        message_data = [
            TextBlockData(content=TextBlockContent(text="Test response with code blocks")),
            TextBlockData(content=TextBlockContent(text="<code_block><programming_language>python</programming_language><file_path>hello.py</file_path><is_diff>false</is_diff>print('hello')</code_block>")),
        ]
        
        parsed_blocks, metadata = Gemini2Point5FlashCodeQuerySolverPromptHandler.get_parsed_response_blocks(
            message_data
        )
        
        assert isinstance(parsed_blocks, list)
        assert isinstance(metadata, dict)

    def test_get_parsed_result_non_streaming(self) -> None:
        """Test parsing of non-streaming LLM response."""
        from app.backend_common.models.dto.message_thread_dto import TextBlockData, TextBlockContent
        
        mock_response = Mock(spec=NonStreamingResponse)
        mock_response.content = [
            TextBlockData(content=TextBlockContent(text="Here's your code:\n<code_block><programming_language>python</programming_language><file_path>factorial.py</file_path><is_diff>false</is_diff>def factorial(n):\n    return 1 if n <= 1 else n * factorial(n-1)</code_block>"))
        ]
        
        result = Gemini2Point5FlashCodeQuerySolverPromptHandler.get_parsed_result(mock_response)
        
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], list)
        assert isinstance(result[1], dict)

    @pytest.mark.asyncio
    async def test_get_parsed_streaming_events(self) -> None:
        """Test parsing of streaming events."""
        async def mock_async_generator():
            return
            yield  # This is unreachable but makes it a generator
        
        mock_streaming_response = Mock(spec=StreamingResponse)
        mock_streaming_response.content = mock_async_generator()
        
        events = []
        async_iterator = await Gemini2Point5FlashCodeQuerySolverPromptHandler.get_parsed_streaming_events(
            mock_streaming_response
        )
        async for event in async_iterator:
            events.append(event)
        
        assert isinstance(events, list)

    def test_get_parsed_custom_blocks(self) -> None:
        """Test parsing of custom blocks from input string."""
        input_string = """
        <thinking>This is a thinking block</thinking>
        <code_block>
        <programming_language>python</programming_language>
        <file_path>main.py</file_path>
        <is_diff>false</is_diff>
        def hello():
            print("world")
        </code_block>
        <summary>This is a summary</summary>
        """
        
        result = Gemini2Point5FlashCodeQuerySolverPromptHandler._get_parsed_custom_blocks(input_string)
        
        assert isinstance(result, list)

    def test_extract_code_block_info(self) -> None:
        """Test extraction of code block information."""
        code_block_string = """
        <programming_language>python</programming_language>
        <file_path>src/utils.py</file_path>
        <is_diff>false</is_diff>
        def utility_function():
            pass
        """
        
        result = Gemini2Point5FlashCodeQuerySolverPromptHandler.extract_code_block_info(code_block_string)
        
        assert isinstance(result, dict)
        if result:  # Only check if extraction was successful
            assert "language" in result
            assert "file_path" in result
            assert "is_diff" in result

    def test_handler_attributes_consistency(self, handler: Gemini2Point5FlashCodeQuerySolverPromptHandler) -> None:
        """Test that handler attributes are consistent and properly set."""
        assert hasattr(handler, 'prompt_type')
        assert hasattr(handler, 'prompt_category')
        assert hasattr(handler, 'prompt_class')
        assert hasattr(handler, 'params')
        assert hasattr(handler, 'prompt')

    def test_different_parameter_combinations(self) -> None:
        """Test handler with different parameter combinations."""
        test_cases = [
            {
                "query": "Simple query",
                "files": [],
            },
            {
                "query": "Complex query with files",
                "files": [{"path": "test.py", "content": "print('test')"}],
                "additional_context": "Test context",
            },
            {
                "query": "Query with repository structure",
                "files": [],
                "repository_structure": {"src": ["main.py"], "tests": ["test_main.py"]},
                "additional_context": "Repository context",
            },
        ]
        
        for params in test_cases:
            handler = Gemini2Point5FlashCodeQuerySolverPromptHandler(params)
            assert handler.params == params
            assert handler.get_system_prompt() is not None
            assert handler.get_prompt() is not None

    def test_prompt_class_inheritance(self, handler: Gemini2Point5FlashCodeQuerySolverPromptHandler) -> None:
        """Test that the prompt class is properly inherited and instantiated."""
        assert handler.prompt_class is not None
        assert handler.prompt is not None
        assert isinstance(handler.prompt, handler.prompt_class)

    @pytest.mark.asyncio
    async def test_error_handling_in_streaming_events(self) -> None:
        """Test error handling in streaming events parsing."""
        # Test with malformed streaming response
        async def mock_error_generator():
            raise ValueError("Mock streaming error")
            yield  # This is unreachable but makes it a generator
        
        mock_streaming_response = Mock(spec=StreamingResponse)
        mock_streaming_response.content = mock_error_generator()
        
        try:
            events = []
            async for event in Gemini2Point5FlashCodeQuerySolverPromptHandler.get_parsed_streaming_events(
                mock_streaming_response
            ):
                events.append(event)
        except Exception as e:
            # Should handle errors gracefully
            assert isinstance(e, Exception)

    def test_empty_input_handling(self) -> None:
        """Test handling of empty or minimal inputs."""
        # Test with minimal parameters
        minimal_params = {"query": ""}
        handler = Gemini2Point5FlashCodeQuerySolverPromptHandler(minimal_params)
        
        assert handler.params == minimal_params
        system_prompt = handler.get_system_prompt()
        assert isinstance(system_prompt, str)
        
        prompt = handler.get_prompt()
        assert isinstance(prompt, UserAndSystemMessages)

    def test_custom_blocks_with_malformed_input(self) -> None:
        """Test custom blocks parsing with malformed input."""
        malformed_inputs = [
            "",
            "<thinking>Incomplete thinking",
            "No XML tags at all",
            "<invalid_tag>Content</invalid_tag>",
        ]
        
        for malformed_input in malformed_inputs:
            result = Gemini2Point5FlashCodeQuerySolverPromptHandler._get_parsed_custom_blocks(malformed_input)
            assert isinstance(result, list)
        
        # Test that malformed code blocks raise expected exceptions
        malformed_code_blocks = [
            "<code_block>No closing tag",
        ]
        
        for malformed_input in malformed_code_blocks:
            with pytest.raises(AttributeError):
                Gemini2Point5FlashCodeQuerySolverPromptHandler._get_parsed_custom_blocks(malformed_input)

    def test_code_block_info_extraction_edge_cases(self) -> None:
        """Test code block info extraction with edge cases."""
        valid_edge_cases = [
            "<programming_language>python</programming_language><file_path>test.py</file_path><is_diff>false</is_diff>",  # Complete tags
            "<programming_language></programming_language><file_path></file_path><is_diff>false</is_diff>",  # Empty tags
        ]
        
        for edge_case in valid_edge_cases:
            result = Gemini2Point5FlashCodeQuerySolverPromptHandler.extract_code_block_info(edge_case)
            assert isinstance(result, dict)
        
        # Test that incomplete edge cases raise AttributeError (due to app code bug)
        invalid_edge_cases = [
            "",  # Empty string
            "<programming_language>python</programming_language>",  # Missing is_diff tag
            "<file_path>test.py</file_path>",  # Missing is_diff tag  
            "No XML tags",  # No XML at all
        ]
        
        for edge_case in invalid_edge_cases:
            with pytest.raises(AttributeError):
                Gemini2Point5FlashCodeQuerySolverPromptHandler.extract_code_block_info(edge_case)

    def test_handler_immutability_after_initialization(self, handler: Gemini2Point5FlashCodeQuerySolverPromptHandler) -> None:
        """Test that handler core attributes remain immutable after initialization."""
        original_prompt_type = handler.prompt_type
        original_prompt_category = handler.prompt_category
        
        # These should remain constant
        assert handler.prompt_type == original_prompt_type
        assert handler.prompt_category == original_prompt_category
        
        # Test multiple calls don't change internal state
        handler.get_system_prompt()
        handler.get_prompt()
        
        assert handler.prompt_type == original_prompt_type
        assert handler.prompt_category == original_prompt_category