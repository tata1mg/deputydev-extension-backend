from typing import Any, Dict, List
from unittest.mock import Mock

from app.main.blueprints.deputy_dev.services.code_review.common.agents.dataclasses.main import (
    AgentAndInitParams,
    AgentTypes,
)
from app.main.blueprints.deputy_dev.services.code_review.common.comments.dataclasses.main import (
    ParsedCommentData,
)


class AgentFactoryFixtures:
    """Fixtures for AgentFactory tests."""

    @staticmethod
    def get_valid_agent_and_init_params() -> AgentAndInitParams:
        """Return a valid AgentAndInitParams instance."""
        return AgentAndInitParams(agent_type=AgentTypes.CODE_MAINTAINABILITY, init_params={"test_param": "test_value"})

    @staticmethod
    def get_multiple_agent_and_init_params() -> List[AgentAndInitParams]:
        """Return multiple AgentAndInitParams instances."""
        return [
            AgentAndInitParams(agent_type=AgentTypes.CODE_MAINTAINABILITY, init_params={"param1": "value1"}),
            AgentAndInitParams(agent_type=AgentTypes.CODE_COMMUNICATION, init_params={"param2": "value2"}),
            AgentAndInitParams(agent_type=AgentTypes.ERROR, init_params={"param3": "value3"}),
        ]

    @staticmethod
    def get_mock_context_service() -> Mock:
        """Return a mock context service."""
        return Mock()

    @staticmethod
    def get_mock_llm_handler() -> Mock:
        """Return a mock LLM handler."""
        return Mock()

    @staticmethod
    def get_mock_parsed_comments() -> List[ParsedCommentData]:
        """Return mock parsed comments."""
        return [Mock(spec=ParsedCommentData), Mock(spec=ParsedCommentData)]

    @staticmethod
    def get_agent_type_mappings() -> Dict[AgentTypes, Any]:
        """Return expected agent type mappings."""
        return {
            AgentTypes.BUSINESS_LOGIC_VALIDATION: "business_logic_agent",
            AgentTypes.CODE_MAINTAINABILITY: "maintainability_agent",
            AgentTypes.CODE_COMMUNICATION: "communication_agent",
            AgentTypes.ERROR: "error_agent",
            AgentTypes.PERFORMANCE_OPTIMIZATION: "performance_agent",
            AgentTypes.SECURITY: "security_agent",
            AgentTypes.PR_SUMMARY: "summary_agent",
            AgentTypes.COMMENT_VALIDATION: "validation_agent",
            AgentTypes.COMMENT_SUMMARIZATION: "summarization_agent",
            AgentTypes.CUSTOM_COMMENTER_AGENT: "custom_agent",
        }

    @staticmethod
    def get_include_agent_types() -> List[AgentTypes]:
        """Return agent types for include filter tests."""
        return [AgentTypes.CODE_MAINTAINABILITY, AgentTypes.ERROR]

    @staticmethod
    def get_exclude_agent_types() -> List[AgentTypes]:
        """Return agent types for exclude filter tests."""
        return [AgentTypes.CODE_COMMUNICATION, AgentTypes.SECURITY]

    @staticmethod
    def get_finalization_agent_types() -> List[AgentTypes]:
        """Return finalization agent types."""
        return [AgentTypes.COMMENT_VALIDATION, AgentTypes.COMMENT_SUMMARIZATION]

    @staticmethod
    def get_code_review_agent_types() -> List[AgentTypes]:
        """Return code review agent types."""
        return [
            AgentTypes.CODE_MAINTAINABILITY,
            AgentTypes.CODE_COMMUNICATION,
            AgentTypes.ERROR,
            AgentTypes.PERFORMANCE_OPTIMIZATION,
            AgentTypes.SECURITY,
            AgentTypes.CUSTOM_COMMENTER_AGENT,
        ]
