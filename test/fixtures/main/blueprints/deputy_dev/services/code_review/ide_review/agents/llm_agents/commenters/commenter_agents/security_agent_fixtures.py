from typing import Any, Dict, List

from deputydev_core.llm_handler.models.dto.message_thread_dto import LLModels


class SecurityAgentFixtures:
    """Fixtures for SecurityAgent tests."""

    @staticmethod
    def get_various_llm_models() -> List[LLModels]:
        """Return various LLM models for testing."""
        return [
            LLModels.CLAUDE_3_POINT_7_SONNET,
            LLModels.CLAUDE_3_POINT_5_SONNET,
            LLModels.CLAUDE_4_SONNET,
            LLModels.GPT_4O,
            LLModels.GPT_4_POINT_1,
        ]

    @staticmethod
    def get_additional_init_kwargs() -> Dict[str, Any]:
        """Return additional initialization kwargs."""
        return {"custom_param": "test_value", "debug_mode": True, "timeout": 30}

    @staticmethod
    def get_empty_tokens_data() -> Dict[str, int]:
        """Return empty tokens data structure."""
        return {}

    @staticmethod
    def get_sample_tokens_data() -> Dict[str, int]:
        """Return sample tokens data structure."""
        return {"pr_title_tokens": 15, "pr_description_tokens": 200, "pr_diff_tokens": 1500}

    @staticmethod
    def get_context_service_mock_data() -> Dict[str, Any]:
        """Return mock data for context service."""
        return {
            "review_id": 123,
            "pr_diff": "sample diff content",
            "pr_title": "Add security improvements",
            "pr_description": "This PR adds security enhancements to the codebase",
        }

    @staticmethod
    def get_llm_handler_mock_data() -> Dict[str, Any]:
        """Return mock data for LLM handler."""
        return {"model_name": "claude-3-sonnet", "max_tokens": 4000, "temperature": 0.1}

    @staticmethod
    def get_security_specific_config() -> Dict[str, Any]:
        """Return security-specific configuration."""
        return {
            "security_rules": [
                "Check for SQL injection vulnerabilities",
                "Validate input sanitization",
                "Review authentication mechanisms",
                "Check for XSS vulnerabilities",
            ],
            "severity_threshold": "medium",
            "scan_patterns": ["*.py", "*.js", "*.ts"],
        }

    @staticmethod
    def get_agent_initialization_scenarios() -> List[Dict[str, Any]]:
        """Return various agent initialization scenarios."""
        return [
            {"name": "basic_init", "model": LLModels.CLAUDE_3_POINT_7_SONNET, "kwargs": {}},
            {
                "name": "with_custom_params",
                "model": LLModels.CLAUDE_4_SONNET,
                "kwargs": {"custom_setting": True, "priority": "high"},
            },
            {
                "name": "with_user_agent",
                "model": LLModels.GPT_4O,
                "kwargs": {"user_agent_dto": {"id": 123, "preferences": {}}},
            },
        ]
