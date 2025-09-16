import pytest
from pydantic import ValidationError

from app.main.blueprints.deputy_dev.constants.constants import IdeReviewCommentStatus
from app.main.blueprints.deputy_dev.services.code_review.ide_review.dataclass.main import (
    AgentRequestItem,
    AgentTaskResult,
    CommentUpdateRequest,
    FileWiseChanges,
    GetRepoIdRequest,
    MultiAgentReviewRequest,
    RequestType,
    ReviewRequest,
    ToolUseResponseData,
    WebSocketMessage,
)
from test.fixtures.main.blueprints.deputy_dev.services.code_review.ide_review.dataclass.main_fixtures import (
    IdeReviewDataclassFixtures,
)


class TestRequestType:
    """Test cases for RequestType enum."""

    def test_request_type_values(self) -> None:
        """Test RequestType enum has correct values."""
        # Assert
        assert RequestType.QUERY == "query"
        assert RequestType.TOOL_USE_RESPONSE == "tool_use_response"
        assert RequestType.TOOL_USE_FAILED == "tool_use_failed"

    def test_request_type_membership(self) -> None:
        """Test RequestType enum membership."""
        # Assert
        assert RequestType.QUERY in RequestType
        assert RequestType.TOOL_USE_RESPONSE in RequestType
        assert RequestType.TOOL_USE_FAILED in RequestType

        # Test with values
        request_type_values = [member.value for member in RequestType]
        assert "query" in request_type_values
        assert "tool_use_response" in request_type_values
        assert "tool_use_failed" in request_type_values
        assert "invalid_type" not in request_type_values


class TestToolUseResponseData:
    """Test cases for ToolUseResponseData model."""

    def test_tool_use_response_data_creation(self) -> None:
        """Test ToolUseResponseData creation with valid data."""
        # Arrange
        data = IdeReviewDataclassFixtures.get_tool_use_response_data()

        # Act
        tool_response = ToolUseResponseData(**data)

        # Assert
        assert tool_response.tool_name == data["tool_name"]
        assert tool_response.tool_use_id == data["tool_use_id"]
        assert tool_response.response == data["response"]

    def test_tool_use_response_data_missing_required_fields(self) -> None:
        """Test ToolUseResponseData raises error with missing required fields."""
        # Arrange
        incomplete_data = {"tool_name": "test_tool"}

        # Act & Assert
        with pytest.raises(ValidationError):
            ToolUseResponseData(**incomplete_data)

    def test_tool_use_response_data_with_complex_response(self) -> None:
        """Test ToolUseResponseData with complex response data."""
        # Arrange
        data = IdeReviewDataclassFixtures.get_tool_use_response_with_complex_data()

        # Act
        tool_response = ToolUseResponseData(**data)

        # Assert
        assert tool_response.tool_name == data["tool_name"]
        assert tool_response.response == data["response"]
        assert isinstance(tool_response.response, dict)


class TestAgentRequestItem:
    """Test cases for AgentRequestItem model."""

    def test_agent_request_item_creation(self) -> None:
        """Test AgentRequestItem creation with valid data."""
        # Arrange
        data = IdeReviewDataclassFixtures.get_agent_request_item_data()

        # Act
        agent_request = AgentRequestItem(**data)

        # Assert
        assert agent_request.agent_id == data["agent_id"]
        assert agent_request.review_id == data["review_id"]
        assert agent_request.type == data["type"]
        assert agent_request.tool_use_response is None

    def test_agent_request_item_with_tool_use_response(self) -> None:
        """Test AgentRequestItem with tool_use_response."""
        # Arrange
        tool_response_data = IdeReviewDataclassFixtures.get_tool_use_response_data()
        tool_response = ToolUseResponseData(**tool_response_data)

        data = IdeReviewDataclassFixtures.get_agent_request_item_data()
        data["tool_use_response"] = tool_response

        # Act
        agent_request = AgentRequestItem(**data)

        # Assert
        assert agent_request.tool_use_response == tool_response

    def test_agent_request_item_invalid_type(self) -> None:
        """Test AgentRequestItem with invalid request type."""
        # Arrange
        data = IdeReviewDataclassFixtures.get_agent_request_item_data()
        data["type"] = "invalid_type"

        # Act & Assert
        with pytest.raises(ValidationError):
            AgentRequestItem(**data)


class TestMultiAgentReviewRequest:
    """Test cases for MultiAgentReviewRequest model."""

    def test_multi_agent_review_request_creation(self) -> None:
        """Test MultiAgentReviewRequest creation with valid data."""
        # Arrange
        data = IdeReviewDataclassFixtures.get_multi_agent_review_request_data()

        # Act
        request = MultiAgentReviewRequest(**data)

        # Assert
        assert len(request.agents) == len(data["agents"])
        assert request.review_id == data["review_id"]
        assert request.connection_id == data["connection_id"]
        assert request.user_team_id == data.get("user_team_id")

    def test_multi_agent_review_request_without_user_team_id(self) -> None:
        """Test MultiAgentReviewRequest without user_team_id."""
        # Arrange
        data = IdeReviewDataclassFixtures.get_multi_agent_review_request_data()
        data.pop("user_team_id", None)

        # Act
        request = MultiAgentReviewRequest(**data)

        # Assert
        assert request.user_team_id is None

    def test_multi_agent_review_request_empty_agents(self) -> None:
        """Test MultiAgentReviewRequest with empty agents list."""
        # Arrange
        data = IdeReviewDataclassFixtures.get_multi_agent_review_request_data()
        data["agents"] = []

        # Act
        request = MultiAgentReviewRequest(**data)

        # Assert
        assert len(request.agents) == 0


class TestAgentTaskResult:
    """Test cases for AgentTaskResult model."""

    def test_agent_task_result_creation(self) -> None:
        """Test AgentTaskResult creation with valid data."""
        # Arrange
        data = IdeReviewDataclassFixtures.get_agent_task_result_data()

        # Act
        result = AgentTaskResult(**data)

        # Assert
        assert result.agent_id == data["agent_id"]
        assert result.agent_name == data["agent_name"]
        assert result.agent_type == data["agent_type"]
        assert result.status == data["status"]
        assert result.result == data["result"]

    def test_agent_task_result_with_optional_fields(self) -> None:
        """Test AgentTaskResult with optional fields."""
        # Arrange
        data = IdeReviewDataclassFixtures.get_agent_task_result_with_optional_fields()

        # Act
        result = AgentTaskResult(**data)

        # Assert
        assert result.tokens_data == data["tokens_data"]
        assert result.model == data["model"]
        assert result.display_name == data["display_name"]
        assert result.error_message == data["error_message"]

    def test_agent_task_result_default_values(self) -> None:
        """Test AgentTaskResult default values for optional fields."""
        # Arrange
        data = IdeReviewDataclassFixtures.get_minimal_agent_task_result_data()

        # Act
        result = AgentTaskResult(**data)

        # Assert
        assert result.tokens_data == {}
        assert result.model == ""
        assert result.display_name == ""
        assert result.error_message is None


class TestWebSocketMessage:
    """Test cases for WebSocketMessage model."""

    def test_websocket_message_creation(self) -> None:
        """Test WebSocketMessage creation with valid data."""
        # Arrange
        data = IdeReviewDataclassFixtures.get_websocket_message_data()

        # Act
        message = WebSocketMessage(**data)

        # Assert
        assert message.type == data["type"]
        assert message.agent_id == data.get("agent_id")
        assert message.data == data.get("data", {})

    def test_websocket_message_minimal(self) -> None:
        """Test WebSocketMessage with minimal data."""
        # Arrange
        data = {"type": "test_message"}

        # Act
        message = WebSocketMessage(**data)

        # Assert
        assert message.type == "test_message"
        assert message.agent_id is None
        assert message.data == {}
        assert message.timestamp is None


class TestFileWiseChanges:
    """Test cases for FileWiseChanges model."""

    def test_file_wise_changes_creation(self) -> None:
        """Test FileWiseChanges creation with valid data."""
        # Arrange
        data = IdeReviewDataclassFixtures.get_file_wise_changes_data()

        # Act
        changes = FileWiseChanges(**data)

        # Assert
        assert changes.file_path == data["file_path"]
        assert changes.file_name == data["file_name"]
        assert changes.status == data["status"]
        assert changes.line_changes == data["line_changes"]
        assert changes.diff == data["diff"]


class TestReviewRequest:
    """Test cases for ReviewRequest model."""

    def test_review_request_creation(self) -> None:
        """Test ReviewRequest creation with valid data."""
        # Arrange
        data = IdeReviewDataclassFixtures.get_review_request_data()

        # Act
        request = ReviewRequest(**data)

        # Assert
        assert request.repo_name == data["repo_name"]
        assert request.origin_url == data["origin_url"]
        assert request.source_branch == data["source_branch"]
        assert request.target_branch == data["target_branch"]
        assert request.review_type == data["review_type"]

    def test_review_request_with_optional_diff_attachment(self) -> None:
        """Test ReviewRequest with optional diff_attachment_id."""
        # Arrange
        data = IdeReviewDataclassFixtures.get_review_request_with_attachment()

        # Act
        request = ReviewRequest(**data)

        # Assert
        assert request.diff_attachment_id == data["diff_attachment_id"]

    def test_review_request_without_diff_attachment(self) -> None:
        """Test ReviewRequest without diff_attachment_id."""
        # Arrange
        data = IdeReviewDataclassFixtures.get_review_request_data()

        # Act
        request = ReviewRequest(**data)

        # Assert
        assert request.diff_attachment_id is None


class TestCommentUpdateRequest:
    """Test cases for CommentUpdateRequest model."""

    def test_comment_update_request_creation(self) -> None:
        """Test CommentUpdateRequest creation with valid data."""
        # Arrange
        data = IdeReviewDataclassFixtures.get_comment_update_request_data()

        # Act
        request = CommentUpdateRequest(**data)

        # Assert
        assert request.id == data["id"]
        assert request.comment_status == data["comment_status"]

    def test_comment_update_request_various_statuses(self) -> None:
        """Test CommentUpdateRequest with various comment statuses."""
        # Arrange
        statuses = [
            IdeReviewCommentStatus.NOT_REVIEWED,
            IdeReviewCommentStatus.ACCEPTED,
            IdeReviewCommentStatus.REJECTED,
        ]

        for status in statuses:
            data = {"id": 123, "comment_status": status}

            # Act
            request = CommentUpdateRequest(**data)

            # Assert
            assert request.comment_status == status


class TestGetRepoIdRequest:
    """Test cases for GetRepoIdRequest model."""

    def test_get_repo_id_request_creation(self) -> None:
        """Test GetRepoIdRequest creation with valid data."""
        # Arrange
        data = IdeReviewDataclassFixtures.get_repo_id_request_data()

        # Act
        request = GetRepoIdRequest(**data)

        # Assert
        assert request.repo_name == data["repo_name"]
        assert request.origin_url == data["origin_url"]

    def test_get_repo_id_request_missing_fields(self) -> None:
        """Test GetRepoIdRequest with missing required fields."""
        # Arrange
        incomplete_data = {"repo_name": "test_repo"}

        # Act & Assert
        with pytest.raises(ValidationError):
            GetRepoIdRequest(**incomplete_data)

    def test_get_repo_id_request_various_urls(self) -> None:
        """Test GetRepoIdRequest with various URL formats."""
        # Arrange
        url_variations = IdeReviewDataclassFixtures.get_various_origin_urls()

        for url in url_variations:
            data = {"repo_name": "test_repo", "origin_url": url}

            # Act
            request = GetRepoIdRequest(**data)

            # Assert
            assert request.origin_url == url
