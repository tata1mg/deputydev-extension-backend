"""Fixture data for Claude 4 Sonnet handler tests."""

from typing import Any, Dict, List

from app.backend_common.models.dto.message_thread_dto import (
    ContentBlockCategory,
    MessageData,
    TextBlockContent,
    TextBlockData,
)


class Claude4SonnetHandlerFixtures:
    """Fixture data for Claude 4 Sonnet handler tests."""

    @staticmethod
    def get_sample_params() -> Dict[str, Any]:
        """Get sample parameters for handler initialization."""
        return {
            "query": "Implement a thread-safe singleton pattern",
            "repositories_context": "class Singleton: pass",
            "file_context": "# Existing singleton implementation",
            "conversation_turns": [],
            "attachments": [],
            "previous_queries": [],
        }

    @staticmethod
    def get_minimal_params() -> Dict[str, Any]:
        """Get minimal parameters for handler initialization."""
        return {
            "query": "Simple query",
            "repositories_context": "",
            "file_context": "",
            "conversation_turns": [],
            "attachments": [],
            "previous_queries": [],
        }

    @staticmethod
    def get_complex_params() -> Dict[str, Any]:
        """Get complex parameters for handler initialization."""
        return {
            "query": "Implement a complex microservices architecture with authentication",
            "repositories_context": "class UserService: pass\nclass AuthService: pass",
            "file_context": "# Complex system architecture",
            "conversation_turns": [
                {"role": "user", "content": "Can you help me design a system?"},
                {"role": "assistant", "content": "I'll help you design a robust system."},
            ],
            "attachments": [{"name": "architecture.md", "content": "# System Architecture\n..."}],
            "previous_queries": ["Design a database schema", "Implement caching layer"],
        }

    @staticmethod
    def get_sample_message_data() -> List[MessageData]:
        """Get sample message data for testing Claude response parsing."""
        return [
            TextBlockData(
                type=ContentBlockCategory.TEXT_BLOCK,
                content=TextBlockContent(
                    text="I'll help you implement a thread-safe singleton pattern with lazy initialization."
                ),
            ),
            TextBlockData(
                type=ContentBlockCategory.TEXT_BLOCK,
                content=TextBlockContent(
                    text="<thinking>Simple thinking content</thinking><code_block><programming_language>python</programming_language><file_path>test.py</file_path><is_diff>false</is_diff>print('hello')</code_block>"
                ),
            ),
        ]

    @staticmethod
    def get_malformed_examples() -> List[str]:
        """Get malformed examples for error handling tests."""
        return [
            "<thinking>Incomplete thinking block without closing tag",
            "Plain text without any XML structure",
            "<thinking></thinking>",  # Empty thinking block
            "<code_block></code_block>",  # Empty code block
        ]

    @staticmethod
    def get_thinking_examples() -> List[str]:
        """Get thinking block examples for testing Claude responses."""
        return [
            "<thinking>The user is asking for a thread-safe singleton pattern.</thinking>",
            "<thinking>For this microservices architecture, I need to consider various approaches.</thinking>",
            "<thinking>The user wants to refactor a class to use composition instead of inheritance.</thinking>",
        ]

    @staticmethod
    def get_summary_examples() -> List[str]:
        """Get summary examples for testing Claude responses."""
        return [
            "<summary>Implemented a thread-safe singleton pattern using double-checked locking.</summary>",
            "<summary>Created a microservices architecture with proper service discovery.</summary>",
            "<summary>Refactored the class to use composition pattern instead of inheritance.</summary>",
        ]

    @staticmethod
    def get_code_block_examples() -> List[str]:
        """Get code block examples for testing Claude responses."""
        return [
            "<code_block><programming_language>python</programming_language><file_path>src/utils/retry.py</file_path><is_diff>false</is_diff>def retry_function(): pass</code_block>",
            "<code_block><programming_language>typescript</programming_language><file_path>src/types/api.ts</file_path><is_diff>true</is_diff>interface ApiResponse { data: any; }</code_block>",
        ]

    @staticmethod
    def get_edge_case_examples() -> List[str]:
        """Get edge case examples for robust testing."""
        return [
            "",  # Empty string
            "<thinking>Incomplete thinking block without closing tag",
            "Plain text without any XML structure",
            "<thinking></thinking>",  # Empty thinking block
            "<code_block></code_block>",  # Empty code block
        ]

    @staticmethod
    def get_mixed_content_examples() -> List[str]:
        """Get examples with mixed content types for comprehensive testing."""
        return [
            "<thinking>I need to implement the algorithm.</thinking><code_block><programming_language>python</programming_language><file_path>src/algorithms/sorting.py</file_path><is_diff>false</is_diff>def quick_sort(arr): return arr</code_block>",
            "Here's my approach: <thinking>The user needs a complete solution.</thinking><code_block><programming_language>python</programming_language><file_path>src/models.py</file_path><is_diff>false</is_diff>class Product: pass</code_block>",
        ]
