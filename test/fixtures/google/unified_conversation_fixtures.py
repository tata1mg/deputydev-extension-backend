"""
Fixtures for testing unified conversation turn methods for Google/Gemini.

This module contains fixtures for testing Google unified conversation turn
processing methods, including various conversation turn types and scenarios.
"""

import base64
from typing import List

import pytest
from deputydev_core.llm_handler.dataclasses.unified_conversation_turn import (
    AssistantConversationTurn,
    ToolConversationTurn,
    UnifiedConversationTurn,
    UnifiedImageConversationTurnContent,
    UnifiedTextConversationTurnContent,
    UnifiedToolRequestConversationTurnContent,
    UnifiedToolResponseConversationTurnContent,
    UserConversationTurn,
)


@pytest.fixture
def user_text_conversation_turn() -> UserConversationTurn:
    """Simple user conversation turn with text content."""
    return UserConversationTurn(content=[UnifiedTextConversationTurnContent(text="What's the weather like today?")])


@pytest.fixture
def user_multimodal_conversation_turn() -> UserConversationTurn:
    """User conversation turn with text and image content."""
    # Create a simple base64 encoded image (1x1 pixel PNG)
    image_data = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
    )

    return UserConversationTurn(
        content=[
            UnifiedTextConversationTurnContent(text="What do you see in this image?"),
            UnifiedImageConversationTurnContent(bytes_data=image_data, image_mimetype="image/png"),
        ]
    )


@pytest.fixture
def assistant_text_conversation_turn() -> AssistantConversationTurn:
    """Simple assistant conversation turn with text content."""
    return AssistantConversationTurn(content=[UnifiedTextConversationTurnContent(text="I can help you with that!")])


@pytest.fixture
def assistant_with_tool_request_turn() -> AssistantConversationTurn:
    """Assistant conversation turn with text and tool request."""
    return AssistantConversationTurn(
        content=[
            UnifiedTextConversationTurnContent(text="Let me check the weather for you."),
            UnifiedToolRequestConversationTurnContent(
                tool_name="get_weather",
                tool_use_id="weather_123",
                tool_input={"location": "New York", "units": "celsius"},
            ),
        ]
    )


@pytest.fixture
def tool_response_conversation_turn() -> ToolConversationTurn:
    """Tool conversation turn with response data."""
    return ToolConversationTurn(
        content=[
            UnifiedToolResponseConversationTurnContent(
                tool_name="get_weather",
                tool_use_id="weather_123",
                tool_use_response={"temperature": "22°C", "condition": "sunny", "humidity": "65%"},
            )
        ]
    )


@pytest.fixture
def multi_tool_response_conversation_turn() -> ToolConversationTurn:
    """Tool conversation turn with multiple tool responses."""
    return ToolConversationTurn(
        content=[
            UnifiedToolResponseConversationTurnContent(
                tool_name="get_weather",
                tool_use_id="weather_123",
                tool_use_response={"temperature": "22°C", "condition": "sunny"},
            ),
            UnifiedToolResponseConversationTurnContent(
                tool_name="get_news",
                tool_use_id="news_456",
                tool_use_response={"headlines": ["Breaking news", "Tech update"]},
            ),
        ]
    )


@pytest.fixture
def assistant_with_multiple_tools() -> AssistantConversationTurn:
    """Assistant conversation turn with multiple tool requests."""
    return AssistantConversationTurn(
        content=[
            UnifiedTextConversationTurnContent(text="I'll help you with multiple tasks."),
            UnifiedToolRequestConversationTurnContent(
                tool_name="search_web", tool_use_id="search_111", tool_input={"query": "Python tutorials", "limit": 5}
            ),
            UnifiedToolRequestConversationTurnContent(
                tool_name="get_weather",
                tool_use_id="weather_222",
                tool_input={"location": "San Francisco", "units": "fahrenheit"},
            ),
            UnifiedToolRequestConversationTurnContent(
                tool_name="calendar_check",
                tool_use_id="calendar_333",
                tool_input={"date": "2024-12-25", "time_zone": "UTC"},
            ),
        ]
    )


@pytest.fixture
def complex_unified_conversation_turns() -> List[UnifiedConversationTurn]:
    """Complex conversation with all turn types for testing."""
    # Create a complex image
    image_data = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
    )

    return [
        UserConversationTurn(
            content=[
                UnifiedTextConversationTurnContent(text="Analyze this image and search for similar ones."),
                UnifiedImageConversationTurnContent(bytes_data=image_data, image_mimetype="image/png"),
            ]
        ),
        AssistantConversationTurn(
            content=[
                UnifiedTextConversationTurnContent(text="I'll analyze the image and search for similar ones."),
                UnifiedToolRequestConversationTurnContent(
                    tool_name="analyze_image",
                    tool_use_id="analyze_789",
                    tool_input={"image_type": "png", "detail_level": "high"},
                ),
                UnifiedToolRequestConversationTurnContent(
                    tool_name="search_images",
                    tool_use_id="search_abc",
                    tool_input={"similarity_threshold": 0.85, "max_results": 10},
                ),
            ]
        ),
        ToolConversationTurn(
            content=[
                UnifiedToolResponseConversationTurnContent(
                    tool_name="analyze_image",
                    tool_use_id="analyze_789",
                    tool_use_response={
                        "description": "A simple 1x1 pixel PNG image",
                        "colors": ["transparent"],
                        "dimensions": "1x1",
                    },
                ),
                UnifiedToolResponseConversationTurnContent(
                    tool_name="search_images",
                    tool_use_id="search_abc",
                    tool_use_response={"results": ["image1.png", "image2.png"], "count": 2},
                ),
            ]
        ),
    ]


@pytest.fixture
def empty_conversation_turns() -> List[UnifiedConversationTurn]:
    """Empty conversation turns list."""
    return []


@pytest.fixture
def single_user_turn() -> List[UnifiedConversationTurn]:
    """Single user conversation turn."""
    return [UserConversationTurn(content=[UnifiedTextConversationTurnContent(text="Hello!")])]


@pytest.fixture
def conversation_with_edge_cases() -> List[UnifiedConversationTurn]:
    """Conversation with edge cases like empty content."""
    return [
        UserConversationTurn(
            content=[
                UnifiedTextConversationTurnContent(text="")  # Empty text
            ]
        ),
        ToolConversationTurn(
            content=[
                UnifiedToolResponseConversationTurnContent(
                    tool_name="complex_tool",
                    tool_use_id="edge_case_123",
                    tool_use_response={
                        "results": [],
                        "metadata": {"nested": {"deeply": {"structure": "test"}}},
                        "null_value": None,
                        "unicode": "🎉 Special characters åøæ",
                    },
                )
            ]
        ),
    ]


@pytest.fixture
def large_conversation_flow() -> List[UnifiedConversationTurn]:
    """Large conversation flow for performance testing."""
    turns = []

    # Generate multiple conversation cycles
    for i in range(10):
        # User turn
        turns.append(UserConversationTurn(content=[UnifiedTextConversationTurnContent(text=f"Request number {i + 1}")]))

        # Assistant turn with tool request
        turns.append(
            AssistantConversationTurn(
                content=[
                    UnifiedTextConversationTurnContent(text=f"Processing request {i + 1}"),
                    UnifiedToolRequestConversationTurnContent(
                        tool_name=f"tool_{i}",
                        tool_use_id=f"tool_{i}_{i + 1}",
                        tool_input={"index": i, "data": f"value_{i}"},
                    ),
                ]
            )
        )

        # Tool response
        turns.append(
            ToolConversationTurn(
                content=[
                    UnifiedToolResponseConversationTurnContent(
                        tool_name=f"tool_{i}",
                        tool_use_id=f"tool_{i}_{i + 1}",
                        tool_use_response={"result": f"Processed {i + 1}", "status": "success"},
                    )
                ]
            )
        )

    return turns
