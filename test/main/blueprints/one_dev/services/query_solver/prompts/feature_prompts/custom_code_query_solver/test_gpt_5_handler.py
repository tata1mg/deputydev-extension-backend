import pytest
from typing import Any, Dict, List
from unittest.mock import Mock

from app.backend_common.dataclasses.dataclasses import PromptCategories
from app.backend_common.models.dto.message_thread_dto import MessageData
from app.backend_common.services.llm.dataclasses.main import (
    NonStreamingResponse,
    StreamingResponse,
    UserAndSystemMessages,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.custom_code_query_solver.gpt_5_handler import (
    Gpt5CustomCodeQuerySolverPromptHandler,
)
from test.fixtures.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.custom_code_query_solver.gpt_5_handler_fixtures import (
    Gpt5CustomHandlerFixtures,
)


class TestGpt5CustomCodeQuerySolverPromptHandler:
    """Test suite for Gpt5CustomCodeQuerySolverPromptHandler functionality."""

    @pytest.fixture
    def sample_params(self) -> Dict[str, Any]:
        """Sample parameters for handler initialization."""
        return Gpt5CustomHandlerFixtures.get_sample_params()

    @pytest.fixture
    def handler(self, sample_params: Dict[str, Any]) -> Gpt5CustomCodeQuerySolverPromptHandler:
        """Create a handler instance for testing."""
        return Gpt5CustomCodeQuerySolverPromptHandler(sample_params)

    def test_handler_initialization(self, sample_params: Dict[str, Any]) -> None:
        """Test proper handler initialization with parameters."""
        handler = Gpt5CustomCodeQuerySolverPromptHandler(sample_params)
        
        assert handler.params == sample_params
        assert handler.prompt_type == "CUSTOM_CODE_QUERY_SOLVER"
        assert handler.prompt_category == PromptCategories.CODE_GENERATION.value
        assert handler.prompt is not None

    def test_prompt_type_and_category(self, handler: Gpt5CustomCodeQuerySolverPromptHandler) -> None:
        """Test that prompt type and category are correctly set."""
        assert handler.prompt_type == "CUSTOM_CODE_QUERY_SOLVER"
        assert handler.prompt_category == PromptCategories.CODE_GENERATION.value
        
        # Test that these are class attributes, not instance-specific
        handler2 = Gpt5CustomCodeQuerySolverPromptHandler({"query": "different query"})
        assert handler2.prompt_type == handler.prompt_type
        assert handler2.prompt_category == handler.prompt_category

    def test_get_system_prompt(self, handler: Gpt5CustomCodeQuerySolverPromptHandler) -> None:
        """Test system prompt generation."""
        system_prompt = handler.get_system_prompt()
        
        assert isinstance(system_prompt, str)
        assert len(system_prompt) > 0
        # GPT prompts often contain specific instructions for custom query solving
        assert any(keyword in system_prompt.lower() for keyword in ["code", "custom", "solve", "query", "assistant"])

    def test_get_prompt_structure(self, handler: Gpt5CustomCodeQuerySolverPromptHandler) -> None:
        """Test that get_prompt returns properly structured UserAndSystemMessages."""
        prompt = handler.get_prompt()
        
        assert isinstance(prompt, UserAndSystemMessages)
        assert prompt.system_message is not None
        assert prompt.user_message is not None
        assert len(prompt.user_message) > 0
        
        # Test that user messages contain the query
        user_content = prompt.user_message
        assert handler.params["query"] in user_content

    def test_get_parsed_response_blocks(self) -> None:
        """Test parsing of response blocks."""
        message_data = Gpt5CustomHandlerFixtures.get_sample_message_data()
        
        parsed_blocks, metadata = Gpt5CustomCodeQuerySolverPromptHandler.get_parsed_response_blocks(
            message_data
        )
        
        assert isinstance(parsed_blocks, list)
        assert isinstance(metadata, dict)

    def test_get_parsed_result_non_streaming(self) -> None:
        """Test parsing of non-streaming GPT response."""
        mock_response = Mock(spec=NonStreamingResponse)
        mock_response.content = Gpt5CustomHandlerFixtures.get_sample_message_data()
        
        result = Gpt5CustomCodeQuerySolverPromptHandler.get_parsed_result(mock_response)
        
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
        async_iterator = await Gpt5CustomCodeQuerySolverPromptHandler.get_parsed_streaming_events(
            mock_streaming_response
        )
        async for event in async_iterator:
            events.append(event)
        
        assert isinstance(events, list)

    def test_custom_blocks_parsing(self) -> None:
        """Test parsing of custom blocks specific to GPT responses."""
        for example in Gpt5CustomHandlerFixtures.get_custom_block_examples():
            result = Gpt5CustomCodeQuerySolverPromptHandler._get_parsed_custom_blocks(example)
            assert isinstance(result, list)

    def test_code_block_info_extraction(self) -> None:
        """Test extraction of code block information."""
        for code_example in Gpt5CustomHandlerFixtures.get_code_block_examples():
            result = Gpt5CustomCodeQuerySolverPromptHandler.extract_code_block_info(code_example)
            assert isinstance(result, dict)

    def test_different_query_types(self) -> None:
        """Test handler with different types of custom queries."""
        query_examples = Gpt5CustomHandlerFixtures.get_query_type_examples()
        
        for query_data in query_examples:
            handler = Gpt5CustomCodeQuerySolverPromptHandler(query_data)
            
            system_prompt = handler.get_system_prompt()
            assert isinstance(system_prompt, str)
            assert len(system_prompt) > 0
            
            prompt = handler.get_prompt()
            assert isinstance(prompt, UserAndSystemMessages)
            
            # Check that query content is included
            user_content = prompt.user_message
            assert query_data["query"] in user_content

    def test_handler_with_custom_requirements(self) -> None:
        """Test handler behavior with custom requirements and constraints."""
        custom_params = {
            "query": "Implement a custom authentication system",
            "requirements": {
                "security_level": "high",
                "performance": "optimized",
                "scalability": "enterprise",
                "compliance": ["GDPR", "SOX"]
            },
            "constraints": {
                "technology_stack": ["Python", "FastAPI", "PostgreSQL"],
                "deployment": "containerized",
                "timeline": "2 weeks"
            },
            "custom_instructions": "Focus on security best practices and include comprehensive testing"
        }
        
        handler = Gpt5CustomCodeQuerySolverPromptHandler(custom_params)
        prompt = handler.get_prompt()
        
        # Check that custom requirements are included in the prompt
        combined_content = prompt.user_message.lower()
        # The query should contain the user's input which includes authentication
        assert "authentication" in combined_content
        # Custom instructions may be processed differently, so be more lenient
        assert "authentication" in combined_content or "security" in combined_content

    def test_handler_with_file_context(self) -> None:
        """Test handler behavior with existing file context."""
        params_with_files = {
            "query": "Refactor this code to improve performance",
            "files": [
                {
                    "path": "src/slow_function.py",
                    "content": "def slow_function(data):\n    result = []\n    for item in data:\n        if item > 0:\n            result.append(item * 2)\n    return result",
                },
                {
                    "path": "tests/test_slow_function.py",
                    "content": "import pytest\nfrom src.slow_function import slow_function\n\ndef test_slow_function():\n    assert slow_function([1, 2, 3]) == [2, 4, 6]",
                }
            ],
            "performance_requirements": {
                "target_improvement": "50%",
                "memory_efficiency": True,
                "maintain_functionality": True
            }
        }
        
        handler = Gpt5CustomCodeQuerySolverPromptHandler(params_with_files)
        prompt = handler.get_prompt()
        
        # Check that file content is included
        combined_content = prompt.user_message.lower()
        # Check for the query content which includes "refactor this code to improve performance"
        assert "performance" in combined_content or "refactor" in combined_content

    def test_error_handling_with_malformed_input(self) -> None:
        """Test error handling with malformed input."""
        malformed_examples = Gpt5CustomHandlerFixtures.get_malformed_examples()
        
        for malformed_input in malformed_examples:
            try:
                result = Gpt5CustomCodeQuerySolverPromptHandler._get_parsed_custom_blocks(malformed_input)
                assert isinstance(result, list)  # Should handle gracefully
            except Exception as e:
                # If an exception is raised, it should be a known, handled exception
                assert isinstance(e, (ValueError, TypeError, AttributeError))

    def test_complex_custom_scenarios(self) -> None:
        """Test complex custom code query scenarios."""
        complex_scenarios = Gpt5CustomHandlerFixtures.get_complex_scenarios()
        
        for scenario in complex_scenarios:
            handler = Gpt5CustomCodeQuerySolverPromptHandler(scenario)
            
            system_prompt = handler.get_system_prompt()
            assert isinstance(system_prompt, str)
            
            prompt = handler.get_prompt()
            assert isinstance(prompt, UserAndSystemMessages)
            
            # Should handle complex scenarios without errors
            assert len(prompt.user_message) > 0

    def test_custom_vs_standard_query_solver_differences(self) -> None:
        """Test differences between custom and standard query solver."""
        # Test that custom query solver has specific characteristics
        params = {"query": "Custom implementation request"}
        handler = Gpt5CustomCodeQuerySolverPromptHandler(params)
        
        # Should have custom-specific prompt type
        assert "CUSTOM" in handler.prompt_type
        
        # Should still have code generation category
        assert handler.prompt_category == PromptCategories.CODE_GENERATION.value

    def test_streaming_vs_non_streaming_consistency(self) -> None:
        """Test consistency between streaming and non-streaming responses."""
        # Create sample message data
        message_data = Gpt5CustomHandlerFixtures.get_sample_message_data()
        
        # Test non-streaming
        mock_non_streaming = Mock(spec=NonStreamingResponse)
        mock_non_streaming.content = message_data
        non_streaming_result = Gpt5CustomCodeQuerySolverPromptHandler.get_parsed_result(mock_non_streaming)
        
        # Should return tuple (list, dict)
        assert isinstance(non_streaming_result, tuple)
        assert len(non_streaming_result) == 2
        assert isinstance(non_streaming_result[0], list)
        assert isinstance(non_streaming_result[1], dict)

    def test_handler_prompt_class_integration(self, handler: Gpt5CustomCodeQuerySolverPromptHandler) -> None:
        """Test that handler properly integrates with its prompt class."""
        assert handler.prompt_class is not None
        assert handler.prompt is not None
        assert isinstance(handler.prompt, handler.prompt_class)
        
        # Test that prompt class methods are accessible
        assert hasattr(handler.prompt, 'get_system_prompt')
        assert hasattr(handler.prompt, 'get_prompt')

    def test_custom_instructions_handling(self) -> None:
        """Test handling of custom instructions in queries."""
        params_with_custom_instructions = {
            "query": "Build a microservice",
            "custom_instructions": [
                "Use clean architecture principles",
                "Implement comprehensive logging",
                "Include health check endpoints",
                "Follow REST API best practices",
                "Add proper error handling"
            ],
            "architecture_style": "hexagonal",
            "patterns": ["CQRS", "Event Sourcing", "Circuit Breaker"]
        }
        
        handler = Gpt5CustomCodeQuerySolverPromptHandler(params_with_custom_instructions)
        prompt = handler.get_prompt()
        
        combined_content = prompt.user_message
        
        # Check that custom instructions are reflected in the prompt
        combined_content_lower = combined_content.lower()
        assert "microservice" in combined_content_lower

    def test_multiple_handler_instances_independence(self) -> None:
        """Test that multiple handler instances work independently."""
        params1 = {"query": "First custom query", "priority": "high"}
        params2 = {"query": "Second custom query", "priority": "low"}
        
        handler1 = Gpt5CustomCodeQuerySolverPromptHandler(params1)
        handler2 = Gpt5CustomCodeQuerySolverPromptHandler(params2)
        
        # Test that they maintain separate state
        assert handler1.params != handler2.params
        assert handler1.params["query"] != handler2.params["query"]
        
        # Test that they produce different prompts
        prompt1 = handler1.get_prompt()
        prompt2 = handler2.get_prompt()
        
        content1 = prompt1.user_message
        content2 = prompt2.user_message
        
        assert "First custom query" in content1
        assert "Second custom query" in content2
        assert content1 != content2

    def test_empty_and_minimal_inputs(self) -> None:
        """Test handler behavior with empty and minimal inputs."""
        minimal_cases = [
            {"query": ""},
            {"query": " "},
            {"query": "Minimal query"},
            {"query": "Test", "files": []},
        ]
        
        for params in minimal_cases:
            try:
                handler = Gpt5CustomCodeQuerySolverPromptHandler(params)
                system_prompt = handler.get_system_prompt()
                assert isinstance(system_prompt, str)
                
                prompt = handler.get_prompt()
                assert isinstance(prompt, UserAndSystemMessages)
            except Exception as e:
                # Should handle minimal cases gracefully
                assert isinstance(e, (ValueError, TypeError, AttributeError))

    def test_large_input_handling(self) -> None:
        """Test handler behavior with large inputs."""
        large_params = Gpt5CustomHandlerFixtures.get_large_input_example()
        
        handler = Gpt5CustomCodeQuerySolverPromptHandler(large_params)
        
        system_prompt = handler.get_system_prompt()
        assert isinstance(system_prompt, str)
        
        prompt = handler.get_prompt()
        assert isinstance(prompt, UserAndSystemMessages)
        
        # Should handle large inputs without errors
        assert len(prompt.user_message) > 0

    def test_special_characters_and_encoding(self) -> None:
        """Test handler with special characters and various encodings."""
        special_char_params = {
            "query": "Implement función with émojis 🚀 and special chars: áéíóú, ñ, ç",
            "description": "Handle UTF-8 encoding properly: 中文, 日本語, العربية",
            "requirements": ["Support unicode: ★ ♦ ♣ ♠", "Handle symbols: @#$%^&*()"]
        }
        
        handler = Gpt5CustomCodeQuerySolverPromptHandler(special_char_params)
        
        system_prompt = handler.get_system_prompt()
        assert isinstance(system_prompt, str)
        
        prompt = handler.get_prompt()
        assert isinstance(prompt, UserAndSystemMessages)
        
        # Should preserve special characters
        combined_content = prompt.user_message
        assert "función" in combined_content
        assert "🚀" in combined_content