"""
Fixtures for testing unified conversation turn methods.

This module contains fixtures for testing OpenAI unified conversation turn
processing methods, including various conversation turn types and scenarios.
"""

import base64
from typing import List

import pytest

from app.backend_common.services.llm.dataclasses.unified_conversation_turn import (
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
                tool_use_response={"headlines": ["Breaking news 1", "Breaking news 2"]},
            ),
        ]
    )


@pytest.fixture
def complex_unified_conversation_turns() -> List[UnifiedConversationTurn]:
    """Complex conversation flow with all turn types."""
    image_data = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
    )

    return [
        # User turn with multimodal content
        UserConversationTurn(
            content=[
                UnifiedTextConversationTurnContent(text="Analyze this image and get weather data"),
                UnifiedImageConversationTurnContent(bytes_data=image_data, image_mimetype="image/png"),
            ]
        ),
        # Assistant turn with tool request
        AssistantConversationTurn(
            content=[
                UnifiedTextConversationTurnContent(text="I'll analyze the image and get weather data."),
                UnifiedToolRequestConversationTurnContent(
                    tool_name="analyze_image",
                    tool_use_id="image_123",
                    tool_input={"image_url": "data:image/png;base64,..."},
                ),
                UnifiedToolRequestConversationTurnContent(
                    tool_name="get_weather", tool_use_id="weather_456", tool_input={"location": "detected_location"}
                ),
            ]
        ),
        # Tool responses
        ToolConversationTurn(
            content=[
                UnifiedToolResponseConversationTurnContent(
                    tool_name="analyze_image",
                    tool_use_id="image_123",
                    tool_use_response={"detected_objects": ["car", "building"], "location": "New York"},
                ),
                UnifiedToolResponseConversationTurnContent(
                    tool_name="get_weather",
                    tool_use_id="weather_456",
                    tool_use_response={"temperature": "18°C", "condition": "cloudy"},
                ),
            ]
        ),
        # Final assistant response
        AssistantConversationTurn(
            content=[
                UnifiedTextConversationTurnContent(
                    text="I can see a car and building in the image, taken in New York. The current weather there is 18°C and cloudy."
                )
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
def assistant_with_multiple_tools() -> AssistantConversationTurn:
    """Assistant turn with multiple tool requests."""
    return AssistantConversationTurn(
        content=[
            UnifiedTextConversationTurnContent(text="I'll help you with multiple tasks."),
            UnifiedToolRequestConversationTurnContent(
                tool_name="search_web",
                tool_use_id="search_1",
                tool_input={"query": "Python tutorials", "max_results": 5},
            ),
            UnifiedToolRequestConversationTurnContent(
                tool_name="get_weather", tool_use_id="weather_1", tool_input={"location": "San Francisco"}
            ),
            UnifiedToolRequestConversationTurnContent(
                tool_name="calendar_check", tool_use_id="calendar_1", tool_input={"date": "2024-01-15"}
            ),
        ]
    )


@pytest.fixture
def conversation_with_edge_cases() -> List[UnifiedConversationTurn]:
    """Conversation turns with edge cases."""
    return [
        # User turn with empty text
        UserConversationTurn(content=[UnifiedTextConversationTurnContent(text="")]),
        # Assistant turn with no content (edge case)
        AssistantConversationTurn(content=[]),
        # Tool turn with complex nested response
        ToolConversationTurn(
            content=[
                UnifiedToolResponseConversationTurnContent(
                    tool_name="complex_processor",
                    tool_use_id="complex_123",
                    tool_use_response={
                        "results": [
                            {"id": 1, "data": {"nested": {"value": "test"}}},
                            {"id": 2, "data": {"array": [1, 2, 3, 4, 5]}},
                        ],
                        "metadata": {"total": 2, "processing_time": 0.543},
                    },
                )
            ]
        ),
    ]


@pytest.fixture
def large_conversation_flow() -> List[UnifiedConversationTurn]:
    """Large conversation flow for performance testing."""
    turns = []

    for i in range(50):
        if i % 3 == 0:
            # User turn
            turns.append(
                UserConversationTurn(content=[UnifiedTextConversationTurnContent(text=f"User message {i + 1}")])
            )
        elif i % 3 == 1:
            # Assistant turn with occasional tool request
            content = [UnifiedTextConversationTurnContent(text=f"Assistant response {i + 1}")]
            if i % 6 == 1:  # Every 6th turn has a tool request
                content.append(
                    UnifiedToolRequestConversationTurnContent(
                        tool_name=f"tool_{i}", tool_use_id=f"tool_id_{i}", tool_input={"param": f"value_{i}"}
                    )
                )
            turns.append(AssistantConversationTurn(content=content))
        else:
            # Tool response (only when there was a tool request)
            if (i - 2) % 6 == 1:
                turns.append(
                    ToolConversationTurn(
                        content=[
                            UnifiedToolResponseConversationTurnContent(
                                tool_name=f"tool_{i - 1}",
                                tool_use_id=f"tool_id_{i - 1}",
                                tool_use_response={"result": f"result_{i}", "status": "success"},
                            )
                        ]
                    )
                )

    return turns
