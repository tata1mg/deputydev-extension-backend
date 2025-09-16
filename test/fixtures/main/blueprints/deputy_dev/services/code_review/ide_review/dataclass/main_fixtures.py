from typing import Dict, Any, List
from app.main.blueprints.deputy_dev.constants.constants import IdeReviewCommentStatus, ReviewType
from app.main.blueprints.deputy_dev.services.code_review.ide_review.dataclass.main import RequestType


class IdeReviewDataclassFixtures:
    """Fixtures for IDE review dataclass tests."""

    @staticmethod
    def get_tool_use_response_data() -> Dict[str, Any]:
        """Return valid tool use response data."""
        return {
            "tool_name": "grep_search",
            "tool_use_id": "tool_123",
            "response": {
                "results": ["result1", "result2"],
                "total": 2
            }
        }

    @staticmethod
    def get_tool_use_response_with_complex_data() -> Dict[str, Any]:
        """Return tool use response with complex response data."""
        return {
            "tool_name": "file_analyzer",
            "tool_use_id": "tool_complex_456",
            "response": {
                "files": [
                    {
                        "path": "src/main.py",
                        "lines": 150,
                        "issues": [
                            {"line": 25, "type": "security", "severity": "high"},
                            {"line": 45, "type": "performance", "severity": "medium"}
                        ]
                    }
                ],
                "summary": {
                    "total_files": 1,
                    "total_issues": 2,
                    "high_severity": 1,
                    "medium_severity": 1
                },
                "metadata": {
                    "analyzed_at": "2023-01-01T12:00:00Z",
                    "analyzer_version": "1.0.0"
                }
            }
        }

    @staticmethod
    def get_agent_request_item_data() -> Dict[str, Any]:
        """Return valid agent request item data."""
        return {
            "agent_id": 1,
            "review_id": 123,
            "type": RequestType.QUERY
        }

    @staticmethod
    def get_multi_agent_review_request_data() -> Dict[str, Any]:
        """Return valid multi-agent review request data."""
        return {
            "agents": [
                {
                    "agent_id": 1,
                    "review_id": 123,
                    "type": RequestType.QUERY
                },
                {
                    "agent_id": 2,
                    "review_id": 123,
                    "type": RequestType.TOOL_USE_RESPONSE
                }
            ],
            "review_id": 123,
            "connection_id": "conn_456",
            "user_team_id": 789
        }

    @staticmethod
    def get_agent_task_result_data() -> Dict[str, Any]:
        """Return valid agent task result data."""
        return {
            "agent_id": 1,
            "agent_name": "security_agent",
            "agent_type": "security",
            "status": "success",
            "result": {
                "comments": ["Security issue found"],
                "confidence": 0.85
            }
        }

    @staticmethod
    def get_agent_task_result_with_optional_fields() -> Dict[str, Any]:
        """Return agent task result with optional fields."""
        return {
            "agent_id": 2,
            "agent_name": "performance_agent",
            "agent_type": "performance",
            "status": "success",
            "result": {"optimizations": 3},
            "tokens_data": {"input_tokens": 1000, "output_tokens": 500},
            "model": "claude-3-sonnet",
            "display_name": "Performance Optimizer",
            "error_message": None
        }

    @staticmethod
    def get_minimal_agent_task_result_data() -> Dict[str, Any]:
        """Return minimal agent task result data."""
        return {
            "agent_id": 3,
            "agent_name": "minimal_agent",
            "agent_type": "general",
            "status": "error",
            "result": {}
        }

    @staticmethod
    def get_websocket_message_data() -> Dict[str, Any]:
        """Return valid websocket message data."""
        return {
            "type": "AGENT_UPDATE",
            "agent_id": 1,
            "data": {
                "progress": 50,
                "message": "Processing..."
            },
            "timestamp": "2023-01-01T12:00:00Z"
        }

    @staticmethod
    def get_file_wise_changes_data() -> Dict[str, Any]:
        """Return valid file wise changes data."""
        return {
            "file_path": "src/main.py",
            "file_name": "main.py",
            "status": "modified",
            "line_changes": {
                "added": 10,
                "removed": 5,
                "modified": 8
            },
            "diff": "@@ -1,5 +1,7 @@\n def hello():\n-    print('Hello')\n+    print('Hello World')\n+    return True"
        }

    @staticmethod
    def get_review_request_data() -> Dict[str, Any]:
        """Return valid review request data."""
        return {
            "repo_name": "test_repo",
            "origin_url": "https://github.com/user/test_repo.git",
            "source_branch": "feature/new-feature",
            "target_branch": "main",
            "source_commit": "abc123",
            "target_commit": "def456",
            "file_wise_diff": [
                {
                    "file_path": "src/main.py",
                    "file_name": "main.py",
                    "status": "modified",
                    "line_changes": {"added": 5, "removed": 2, "modified": 3},
                    "diff": "@@ -1,3 +1,6 @@\n+new line\n existing line\n-removed line"
                }
            ],
            "review_type": ReviewType.ALL
        }

    @staticmethod
    def get_review_request_with_attachment() -> Dict[str, Any]:
        """Return review request with diff attachment."""
        data = IdeReviewDataclassFixtures.get_review_request_data()
        data["diff_attachment_id"] = "attachment_789"
        return data

    @staticmethod
    def get_comment_update_request_data() -> Dict[str, Any]:
        """Return valid comment update request data."""
        return {
            "id": 123,
            "comment_status": IdeReviewCommentStatus.ACCEPTED
        }

    @staticmethod
    def get_repo_id_request_data() -> Dict[str, Any]:
        """Return valid repo ID request data."""
        return {
            "repo_name": "test_repository",
            "origin_url": "https://github.com/organization/test_repository.git"
        }

    @staticmethod
    def get_various_origin_urls() -> List[str]:
        """Return various origin URL formats."""
        return [
            "https://github.com/user/repo.git",
            "git@github.com:user/repo.git",
            "https://gitlab.com/user/repo.git",
            "git@gitlab.com:user/repo.git",
            "https://bitbucket.org/user/repo.git",
            "git@bitbucket.org:user/repo.git"
        ]

    @staticmethod
    def get_various_request_types() -> List[RequestType]:
        """Return all request types."""
        return [
            RequestType.QUERY,
            RequestType.TOOL_USE_RESPONSE,
            RequestType.TOOL_USE_FAILED
        ]

    @staticmethod
    def get_various_comment_statuses() -> List[IdeReviewCommentStatus]:
        """Return various comment statuses."""
        return [
            IdeReviewCommentStatus.PENDING,
            IdeReviewCommentStatus.APPROVED,
            IdeReviewCommentStatus.DISMISSED
        ]

    @staticmethod
    def get_various_review_types() -> List[ReviewType]:
        """Return various review types."""
        return [
            ReviewType.FULL_REVIEW,
            ReviewType.FOCUSED_REVIEW
        ]

    @staticmethod
    def get_websocket_message_types() -> List[str]:
        """Return various websocket message types."""
        return [
            "AGENT_START",
            "AGENT_UPDATE",
            "AGENT_COMPLETE",
            "AGENT_ERROR",
            "STREAM_END",
            "TOOL_USE_REQUEST",
            "TOOL_USE_RESPONSE"
        ]

    @staticmethod
    def get_agent_statuses() -> List[str]:
        """Return various agent statuses."""
        return [
            "success",
            "error",
            "tool_use_request",
            "pending",
            "running",
            "cancelled"
        ]

    @staticmethod
    def get_file_statuses() -> List[str]:
        """Return various file statuses."""
        return [
            "modified",
            "added",
            "deleted",
            "renamed",
            "copied"
        ]