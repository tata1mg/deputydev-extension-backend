from typing import Dict, Any, List


class PostProcessWebSocketManagerFixtures:
    """Fixtures for PostProcessWebSocketManager tests."""

    @staticmethod
    def get_valid_request_data() -> Dict[str, Any]:
        """Return valid request data for post-processing."""
        return {
            "review_id": 123,
            "user_team_id": "team_456",
            "project_id": "project_789",
            "additional_data": {
                "config": "test_config",
                "options": ["option1", "option2"]
            }
        }

    @staticmethod
    def get_request_data_without_review_id() -> Dict[str, Any]:
        """Return request data missing review_id."""
        return {
            "user_team_id": "team_456",
            "project_id": "project_789"
        }

    @staticmethod
    def get_request_data_with_user_team_id() -> Dict[str, Any]:
        """Return request data with user_team_id."""
        return {
            "review_id": 456,
            "user_team_id": "team_123",
            "project_name": "test_project"
        }

    @staticmethod
    def get_request_data_without_user_team_id() -> Dict[str, Any]:
        """Return request data without user_team_id."""
        return {
            "review_id": 789,
            "project_id": "project_999"
        }

    @staticmethod
    def get_empty_stream_buffer() -> Dict[str, List[str]]:
        """Return empty stream buffer for local testing."""
        return {"messages": []}

    @staticmethod
    def get_stream_buffer_with_messages() -> Dict[str, List[str]]:
        """Return stream buffer with existing messages."""
        return {
            "messages": [
                "Previous message 1",
                "Previous message 2"
            ]
        }

    @staticmethod
    def get_sample_post_process_result() -> Dict[str, Any]:
        """Return sample post-process result."""
        return {
            "status": "SUCCESS",
            "processed_files": ["file1.py", "file2.py"],
            "issues_found": 3,
            "issues_fixed": 2,
            "processing_time": 15.5,
            "summary": "Post-processing completed successfully with 2 fixes applied"
        }

    @staticmethod
    def get_complex_post_process_result() -> Dict[str, Any]:
        """Return complex post-process result with nested data."""
        return {
            "status": "PARTIAL_SUCCESS",
            "results": {
                "analysis": {
                    "total_lines": 1500,
                    "code_coverage": 85.2,
                    "complexity_score": 3.4
                },
                "fixes": [
                    {
                        "file": "main.py",
                        "line": 45,
                        "type": "security",
                        "description": "Fixed SQL injection vulnerability"
                    },
                    {
                        "file": "utils.py",
                        "line": 12,
                        "type": "performance",
                        "description": "Optimized loop performance"
                    }
                ],
                "warnings": [
                    {
                        "file": "config.py",
                        "line": 8,
                        "message": "Deprecated function usage"
                    }
                ]
            },
            "metadata": {
                "processor_version": "1.2.3",
                "timestamp": "2023-01-01T12:00:00Z",
                "execution_time": 32.1
            }
        }

    @staticmethod
    def get_various_connection_ids() -> List[str]:
        """Return various connection IDs for testing."""
        return [
            "conn_123",
            "test_connection_456",
            "websocket_789",
            "local_test_999",
            "",
            "very_long_connection_id_with_special_chars_@#$%"
        ]

    @staticmethod
    def get_various_review_ids() -> List[int]:
        """Return various review IDs for testing."""
        return [1, 123, 456, 789, 0, -1, 9999999]

    @staticmethod
    def get_error_scenarios() -> List[Dict[str, Any]]:
        """Return various error scenarios for testing."""
        return [
            {
                "name": "missing_review_id",
                "request_data": {"user_team_id": "team_123"},
                "expected_error": "review_id is required"
            },
            {
                "name": "invalid_review_id",
                "request_data": {"review_id": "invalid", "user_team_id": "team_123"},
                "expected_error": "Invalid review_id format"
            },
            {
                "name": "empty_request",
                "request_data": {},
                "expected_error": "review_id is required"
            }
        ]

    @staticmethod
    def get_websocket_message_types() -> List[str]:
        """Return expected WebSocket message types."""
        return [
            "POST_PROCESS_START",
            "POST_PROCESS_COMPLETE",
            "POST_PROCESS_ERROR",
            "STREAM_END"
        ]

    @staticmethod
    def get_start_message_data() -> Dict[str, Any]:
        """Return expected start message data."""
        return {"message": "Post-processing started"}

    @staticmethod
    def get_complete_message_data() -> Dict[str, Any]:
        """Return expected complete message data."""
        return {
            "message": "Post-processing completed successfully",
            "result": {"status": "SUCCESS"},
            "progress": 100
        }

    @staticmethod
    def get_error_message_data() -> Dict[str, Any]:
        """Return expected error message data."""
        return {"message": "Post-processing failed: Test error"}

    @staticmethod
    def get_stream_end_message_data() -> Dict[str, Any]:
        """Return expected stream end message data."""
        return {"message": "Post-processing stream ended"}