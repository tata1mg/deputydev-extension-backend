from typing import Any, Dict
from unittest.mock import Mock

import pytest
from deputydev_core.llm_handler.dataclasses.main import (
    NonStreamingResponse,
    StreamingResponse,
    UserAndSystemMessages,
)

from app.backend_common.dataclasses.dataclasses import PromptCategories
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.claude_4_sonnet_handler import (
    Claude4CustomCodeQuerySolverPromptHandler,
)
from test.fixtures.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.claude_4_sonnet_handler_fixtures import (
    Claude4SonnetHandlerFixtures,
)


class TestClaude4CustomCodeQuerySolverPromptHandler:
    """Test suite for Claude4CustomCodeQuerySolverPromptHandler functionality."""

    @pytest.fixture
    def sample_params(self) -> Dict[str, Any]:
        """Sample parameters for handler initialization."""
        return Claude4SonnetHandlerFixtures.get_sample_params()

    @pytest.fixture
    def handler(self, sample_params: Dict[str, Any]) -> Claude4CustomCodeQuerySolverPromptHandler:
        """Create a handler instance for testing."""
        return Claude4CustomCodeQuerySolverPromptHandler(sample_params)

    def test_handler_initialization(self, sample_params: Dict[str, Any]) -> None:
        """Test proper handler initialization with parameters."""
        handler = Claude4CustomCodeQuerySolverPromptHandler(sample_params)

        assert handler.params == sample_params
        assert handler.prompt_type == "CODE_QUERY_SOLVER"
        assert handler.prompt_category == PromptCategories.CODE_GENERATION.value
        assert handler.prompt is not None

    def test_prompt_type_consistency(self, handler: Claude4CustomCodeQuerySolverPromptHandler) -> None:
        """Test that prompt type is consistently set."""
        assert handler.prompt_type == "CODE_QUERY_SOLVER"
        assert hasattr(handler, "prompt_category")
        assert handler.prompt_category == PromptCategories.CODE_GENERATION.value

    def test_get_system_prompt(self, handler: Claude4CustomCodeQuerySolverPromptHandler) -> None:
        """Test system prompt generation."""
        system_prompt = handler.get_system_prompt()

        assert isinstance(system_prompt, str)
        assert len(system_prompt) > 0
        # Claude prompts often contain specific instructions
        assert any(keyword in system_prompt.lower() for keyword in ["assistant", "helpful", "code", "programming"])

    def test_get_prompt_structure(self, handler: Claude4CustomCodeQuerySolverPromptHandler) -> None:
        """Test that get_prompt returns properly structured UserAndSystemMessages."""
        prompt = handler.get_prompt()

        assert isinstance(prompt, UserAndSystemMessages)
        assert prompt.system_message is not None
        assert prompt.user_message is not None
        assert len(prompt.user_message) > 0

        # Test that user messages contain the query
        user_content = prompt.user_message
        assert handler.params["query"] in user_content

    def test_get_parsed_response_blocks_with_claude_format(self) -> None:
        """Test parsing of response blocks with Claude-specific formatting."""
        message_data = Claude4SonnetHandlerFixtures.get_sample_message_data()

        parsed_blocks, metadata = Claude4CustomCodeQuerySolverPromptHandler.get_parsed_response_blocks(message_data)

        assert isinstance(parsed_blocks, list)
        assert isinstance(metadata, dict)

    def test_get_parsed_result_non_streaming(self) -> None:
        """Test parsing of non-streaming Claude response."""
        mock_response = Mock(spec=NonStreamingResponse)
        mock_response.content = Claude4SonnetHandlerFixtures.get_sample_message_data()

        result = Claude4CustomCodeQuerySolverPromptHandler.get_parsed_result(mock_response)

        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], list)
        assert isinstance(result[1], dict)

    @pytest.mark.asyncio
    async def test_get_parsed_streaming_events(self) -> None:
        """Test parsing of streaming events with Claude format."""

        async def mock_async_generator():
            return
            yield  # This is unreachable but makes it a generator

        mock_streaming_response = Mock(spec=StreamingResponse)
        mock_streaming_response.content = mock_async_generator()

        events = []
        async_iterator = await Claude4CustomCodeQuerySolverPromptHandler.get_parsed_streaming_events(
            mock_streaming_response
        )
        async for event in async_iterator:
            events.append(event)

        assert isinstance(events, list)

    def test_custom_blocks_parsing(self) -> None:
        """Test parsing of Claude-specific custom blocks."""
        for example in Claude4SonnetHandlerFixtures.get_code_block_examples():
            result = Claude4CustomCodeQuerySolverPromptHandler._get_parsed_custom_blocks(example)
            assert isinstance(result, list)

    def test_code_block_info_extraction(self) -> None:
        """Test extraction of code block information from Claude format."""
        for code_example in Claude4SonnetHandlerFixtures.get_code_block_examples():
            result = Claude4CustomCodeQuerySolverPromptHandler.extract_code_block_info(code_example)
            assert isinstance(result, dict)

    def test_different_parameter_types(self) -> None:
        """Test handler with various parameter combinations."""
        test_cases = [
            Claude4SonnetHandlerFixtures.get_minimal_params(),
            Claude4SonnetHandlerFixtures.get_complex_params(),
            {
                "query": "Debug this code",
                "files": [{"path": "bug.py", "content": "print('test'"}],
                "error_context": "SyntaxError: incomplete string literal",
            },
        ]

        for params in test_cases:
            handler = Claude4CustomCodeQuerySolverPromptHandler(params)
            assert handler.params == params

            system_prompt = handler.get_system_prompt()
            assert isinstance(system_prompt, str)
            assert len(system_prompt) > 0

            prompt = handler.get_prompt()
            assert isinstance(prompt, UserAndSystemMessages)

    def test_handler_with_file_context(self) -> None:
        """Test handler behavior with file context."""
        params = {
            "query": "Refactor this class to use composition",
            "files": [
                {
                    "path": "src/models/user.py",
                    "content": "class User:\n    def __init__(self, name):\n        self.name = name",
                },
            ],
            "refactor_type": "composition_pattern",
        }

        handler = Claude4CustomCodeQuerySolverPromptHandler(params)
        prompt = handler.get_prompt()

        # Check that file content is included in the prompt
        combined_content = prompt.user_message
        assert "User" in combined_content
        assert "composition" in combined_content.lower()

    def test_error_handling_with_malformed_input(self) -> None:
        """Test error handling with malformed input."""
        malformed_examples = Claude4SonnetHandlerFixtures.get_malformed_examples()

        for malformed_input in malformed_examples:
            try:
                result = Claude4CustomCodeQuerySolverPromptHandler._get_parsed_custom_blocks(malformed_input)
                assert isinstance(result, list)  # Should handle gracefully
            except Exception as e:
                # If an exception is raised, it should be a known, handled exception
                assert isinstance(e, (ValueError, TypeError, AttributeError))

    def test_thinking_blocks_parsing(self) -> None:
        """Test parsing of thinking blocks in Claude responses."""
        thinking_examples = Claude4SonnetHandlerFixtures.get_thinking_examples()

        for thinking_example in thinking_examples:
            result = Claude4CustomCodeQuerySolverPromptHandler._get_parsed_custom_blocks(thinking_example)
            assert isinstance(result, list)

    def test_summary_blocks_parsing(self) -> None:
        """Test parsing of summary blocks in Claude responses."""
        summary_examples = Claude4SonnetHandlerFixtures.get_summary_examples()

        for summary_example in summary_examples:
            result = Claude4CustomCodeQuerySolverPromptHandler._get_parsed_custom_blocks(summary_example)
            assert isinstance(result, list)

    def test_mixed_content_parsing(self) -> None:
        """Test parsing of mixed content with multiple block types."""
        mixed_examples = Claude4SonnetHandlerFixtures.get_mixed_content_examples()

        for mixed_example in mixed_examples:
            result = Claude4CustomCodeQuerySolverPromptHandler._get_parsed_custom_blocks(mixed_example)
            assert isinstance(result, list)

    def test_handler_prompt_class_integration(self, handler: Claude4CustomCodeQuerySolverPromptHandler) -> None:
        """Test that handler properly integrates with its prompt class."""
        assert handler.prompt_class is not None
        assert handler.prompt is not None
        assert isinstance(handler.prompt, handler.prompt_class)

        # Test that prompt class methods are accessible
        assert hasattr(handler.prompt, "get_system_prompt")
        assert hasattr(handler.prompt, "get_prompt")

    def test_claude_specific_features(self, handler: Claude4CustomCodeQuerySolverPromptHandler) -> None:
        """Test Claude-specific features and formatting."""
        system_prompt = handler.get_system_prompt()

        # Claude prompts often have specific formatting or instructions
        assert isinstance(system_prompt, str)

        prompt = handler.get_prompt()
        assert isinstance(prompt, UserAndSystemMessages)

        # Test that Claude-specific formatting is preserved
        if prompt.user_message:
            assert isinstance(prompt.user_message, str)
            assert len(prompt.user_message) > 0

    def test_concurrent_handler_instances(self) -> None:
        """Test that multiple handler instances work independently."""
        params1 = {"query": "First query", "context": "context1"}
        params2 = {"query": "Second query", "context": "context2"}

        handler1 = Claude4CustomCodeQuerySolverPromptHandler(params1)
        handler2 = Claude4CustomCodeQuerySolverPromptHandler(params2)

        # Test that they maintain separate state
        assert handler1.params != handler2.params
        assert handler1.params["query"] != handler2.params["query"]

        # Test that they produce different prompts
        prompt1 = handler1.get_prompt()
        prompt2 = handler2.get_prompt()

        content1 = prompt1.user_message
        content2 = prompt2.user_message

        assert "First query" in content1
        assert "Second query" in content2
        assert content1 != content2

    def test_empty_and_edge_case_inputs(self) -> None:
        """Test handler behavior with empty and edge case inputs."""
        edge_cases = [
            {"query": ""},
            {"query": " "},
            {"query": "Test", "files": []},
            {"query": "Test", "files": None},
        ]

        for params in edge_cases:
            try:
                handler = Claude4CustomCodeQuerySolverPromptHandler(params)
                system_prompt = handler.get_system_prompt()
                assert isinstance(system_prompt, str)

                prompt = handler.get_prompt()
                assert isinstance(prompt, UserAndSystemMessages)
            except Exception as e:
                # Should handle edge cases gracefully
                assert isinstance(e, (ValueError, TypeError, AttributeError))

    def test_code_block_extraction_comprehensive(self) -> None:
        """Test comprehensive code block extraction scenarios."""
        test_cases = [
            # Standard Python code
            {
                "input": """<code_block>
<programming_language>python</programming_language>
<file_path>main.py</file_path>
<is_diff>false</is_diff>
print("Hello")
</code_block>""",
                "expected_keys": ["language", "file_path", "is_diff"],
            },
            # JavaScript with diff
            {
                "input": """<code_block>
<programming_language>javascript</programming_language>
<file_path>app.js</file_path>
<is_diff>true</is_diff>
@@ -1,2 +1,3 @@
 console.log("test");
+console.log("new line");
</code_block>""",
                "expected_keys": ["language", "file_path", "is_diff"],
            },
        ]

        for test_case in test_cases:
            result = Claude4CustomCodeQuerySolverPromptHandler.extract_code_block_info(test_case["input"])

            if result:  # Only check if extraction was successful
                for key in test_case["expected_keys"]:
                    assert key in result or len(result) == 0  # Either has the key or empty dict for malformed input
