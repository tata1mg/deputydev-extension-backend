"""
OpenAI LLM Provider fixtures package.

This package contains fixtures for testing OpenAI LLM provider functionality,
organized by event type and use case.
"""

# Import all fixtures to make them available when importing the package
from .conversation_turns_fixtures import (
    assistant_text_message,
    attachment_data_task_map_empty,
    attachment_data_task_map_with_document,
    attachment_data_task_map_with_image,
    complex_conversation_history,
    conversation_with_multiple_tool_calls,
    message_with_extended_thinking,
    message_with_file_attachment,
    mixed_content_message,
    mock_document_attachment_data,
    mock_image_attachment_data,
    out_of_order_tool_conversation,
    simple_conversation_history,
    simple_text_message,
    tool_use_request_message,
    tool_use_response_message,
)
from .edge_case_fixtures import (
    create_usage_event,
    mock_output_item_added_unknown_type,
    mock_unknown_event,
)
from .function_call_fixtures import (
    create_function_arguments_delta_event,
    create_function_call_added_event,
    mock_function_arguments_delta_event,
    mock_function_arguments_done_event,
    mock_function_call_added_event,
)
from .provider_fixtures import (
    openai_provider,
)
from .response_parsing_fixtures import (
    empty_llm_payload,
    malformed_llm_payload,
    mock_llm_payload,
    mock_llm_payload_complex,
    mock_llm_payload_with_tools,
    mock_openai_response,
    mock_openai_response_new_format,
    mock_openai_response_new_format_with_function,
    mock_openai_response_with_function_call,
    mock_openai_response_without_usage,
    mock_streaming_response,
    sample_content_for_token_counting,
)
from .stream_event_fixtures import (
    mock_response_completed_event,
    mock_response_completed_incomplete_usage,
    mock_response_completed_without_usage,
)
from .text_event_fixtures import (
    create_text_delta_event,
    mock_message_added_event,
    mock_output_text_delta_event,
    mock_output_text_done_event,
)
from .unified_conversation_fixtures import (
    assistant_text_conversation_turn,
    assistant_with_multiple_tools,
    assistant_with_tool_request_turn,
    complex_unified_conversation_turns,
    conversation_with_edge_cases,
    empty_conversation_turns,
    large_conversation_flow,
    multi_tool_response_conversation_turn,
    single_user_turn,
    tool_response_conversation_turn,
    user_multimodal_conversation_turn,
    user_text_conversation_turn,
)

__all__ = [
    # Stream event fixtures
    "mock_response_completed_event",
    "mock_response_completed_without_usage",
    "mock_response_completed_incomplete_usage",
    # Function call fixtures
    "mock_function_call_added_event",
    "mock_function_arguments_delta_event",
    "mock_function_arguments_done_event",
    "create_function_call_added_event",
    "create_function_arguments_delta_event",
    # Text event fixtures
    "mock_message_added_event",
    "mock_output_text_delta_event",
    "mock_output_text_done_event",
    "create_text_delta_event",
    # Edge case fixtures
    "mock_unknown_event",
    "mock_output_item_added_unknown_type",
    "create_usage_event",
    # Provider fixtures
    "openai_provider",
    # Conversation turns fixtures
    "simple_text_message",
    "assistant_text_message",
    "tool_use_request_message",
    "tool_use_response_message",
    "message_with_file_attachment",
    "message_with_extended_thinking",
    "mixed_content_message",
    "simple_conversation_history",
    "complex_conversation_history",
    "conversation_with_multiple_tool_calls",
    "mock_image_attachment_data",
    "mock_document_attachment_data",
    "attachment_data_task_map_empty",
    "attachment_data_task_map_with_image",
    "attachment_data_task_map_with_document",
    "out_of_order_tool_conversation",
    # Response parsing fixtures
    "mock_openai_response",
    "mock_openai_response_with_function_call",
    "mock_openai_response_new_format",
    "mock_openai_response_new_format_with_function",
    "mock_openai_response_without_usage",
    "mock_streaming_response",
    "mock_llm_payload",
    "mock_llm_payload_with_tools",
    "mock_llm_payload_complex",
    "sample_content_for_token_counting",
    "empty_llm_payload",
    "malformed_llm_payload",
    # Unified conversation fixtures
    "user_text_conversation_turn",
    "user_multimodal_conversation_turn",
    "assistant_text_conversation_turn",
    "assistant_with_tool_request_turn",
    "tool_response_conversation_turn",
    "multi_tool_response_conversation_turn",
    "complex_unified_conversation_turns",
    "empty_conversation_turns",
    "single_user_turn",
    "assistant_with_multiple_tools",
    "conversation_with_edge_cases",
    "large_conversation_flow",
]
