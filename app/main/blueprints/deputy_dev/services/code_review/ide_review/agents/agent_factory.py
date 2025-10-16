from typing import List, Optional

from deputydev_core.llm_handler.core.handler import LLMHandler
from deputydev_core.llm_handler.models.dto.message_thread_dto import LLModels

from app.main.blueprints.deputy_dev.models.dto.user_agent_dto import UserAgentDTO
from app.main.blueprints.deputy_dev.services.code_review.common.agents.dataclasses.main import (
    AgentAndInitParams,
    AgentTypes,
)
from app.main.blueprints.deputy_dev.services.code_review.common.comments.dataclasses.main import (
    ParsedCommentData,
)
from app.main.blueprints.deputy_dev.services.code_review.common.prompts.dataclasses.main import (
    PromptFeatures,
)
from app.main.blueprints.deputy_dev.services.code_review.ide_review.agents.llm_agents.comment_summarizer.comment_summarizer_agent import (
    CommentSummarizerAgent,
)
from app.main.blueprints.deputy_dev.services.code_review.ide_review.agents.llm_agents.comment_validator.comment_validator_agent import (
    CommentValidatorAgent,
)
from app.main.blueprints.deputy_dev.services.code_review.ide_review.agents.llm_agents.commenters.base_commentor import (
    BaseCommenterAgent,
)
from app.main.blueprints.deputy_dev.services.code_review.ide_review.agents.llm_agents.commenters.commenter_agents.code_communication_agent import (
    CodeCommunicationAgent,
)
from app.main.blueprints.deputy_dev.services.code_review.ide_review.agents.llm_agents.commenters.commenter_agents.code_maintainability_agent import (
    CodeMaintainabilityAgent,
)
from app.main.blueprints.deputy_dev.services.code_review.ide_review.agents.llm_agents.commenters.commenter_agents.custom_agent import (
    CustomAgent,
)
from app.main.blueprints.deputy_dev.services.code_review.ide_review.agents.llm_agents.commenters.commenter_agents.error_agent import (
    ErrorAgent,
)
from app.main.blueprints.deputy_dev.services.code_review.ide_review.agents.llm_agents.commenters.commenter_agents.performance_optimization_agent import (
    PerformanceOptimizationAgent,
)
from app.main.blueprints.deputy_dev.services.code_review.ide_review.agents.llm_agents.commenters.commenter_agents.security_agent import (
    SecurityAgent,
)
from app.main.blueprints.deputy_dev.services.code_review.ide_review.context.ide_review_context_service import (
    IdeReviewContextService,
)


class AgentFactory:
    agent_type_to_model_map = {
        AgentTypes.BUSINESS_LOGIC_VALIDATION: LLModels.CLAUDE_4_POINT_5_SONNET,
        AgentTypes.CODE_MAINTAINABILITY: LLModels.CLAUDE_4_POINT_5_SONNET,
        AgentTypes.CODE_COMMUNICATION: LLModels.CLAUDE_4_POINT_5_SONNET,
        AgentTypes.ERROR: LLModels.CLAUDE_4_POINT_5_SONNET,
        AgentTypes.PERFORMANCE_OPTIMIZATION: LLModels.CLAUDE_4_POINT_5_SONNET,
        AgentTypes.SECURITY: LLModels.CLAUDE_4_POINT_5_SONNET,
        AgentTypes.PR_SUMMARY: LLModels.GPT_4O,
        AgentTypes.COMMENT_VALIDATION: LLModels.GPT_4_POINT_1,
        AgentTypes.COMMENT_SUMMARIZATION: LLModels.GPT_4_POINT_1,
        AgentTypes.CUSTOM_COMMENTER_AGENT: LLModels.CLAUDE_4_POINT_5_SONNET,
    }

    code_review_agents = {
        AgentTypes.CODE_MAINTAINABILITY: CodeMaintainabilityAgent,
        AgentTypes.CODE_COMMUNICATION: CodeCommunicationAgent,
        AgentTypes.ERROR: ErrorAgent,
        AgentTypes.PERFORMANCE_OPTIMIZATION: PerformanceOptimizationAgent,
        AgentTypes.SECURITY: SecurityAgent,
        # AgentTypes.PR_SUMMARY: PRSummarizerAgent,
        AgentTypes.CUSTOM_COMMENTER_AGENT: CustomAgent,
    }

    review_finalization_agents = {
        AgentTypes.COMMENT_VALIDATION: CommentValidatorAgent,
        AgentTypes.COMMENT_SUMMARIZATION: CommentSummarizerAgent,
    }

    @classmethod
    def get_code_review_agent(
        cls,
        agent_and_init_params: AgentAndInitParams,
        context_service: IdeReviewContextService,
        llm_handler: LLMHandler[PromptFeatures],
        user_agent_dto: Optional[UserAgentDTO] = None,
    ) -> Optional[BaseCommenterAgent]:
        """
        Create a single extension review agent instance.

        Args:
            agent_and_init_params: Agent configuration and initialization parameters
            context_service: Extension context service
            llm_handler: LLM handler instance
            user_agent_dto: Optional user agent configuration

        Returns:
            Single agent instance or None if creation fails
        """

        agent = cls.code_review_agents[agent_and_init_params.agent_type](
            context_service=context_service,
            llm_handler=llm_handler,
            model=cls.agent_type_to_model_map[agent_and_init_params.agent_type],
            user_agent_dto=user_agent_dto,
            **agent_and_init_params.init_params,
        )

        return agent

    @classmethod
    def comment_validation_agent(
        cls,
        context_service: IdeReviewContextService,
        comments: List[ParsedCommentData],
        llm_handler: LLMHandler[PromptFeatures],
    ) -> CommentValidatorAgent:
        model = cls.agent_type_to_model_map[AgentTypes.COMMENT_VALIDATION]
        return CommentValidatorAgent(
            context_service=context_service, comments=comments, llm_handler=llm_handler, model=model
        )

    @classmethod
    def comment_summarization_agent(
        cls,
        context_service: IdeReviewContextService,
        comments: List[ParsedCommentData],
        llm_handler: LLMHandler[PromptFeatures],
    ) -> CommentSummarizerAgent:
        model = cls.agent_type_to_model_map[AgentTypes.COMMENT_SUMMARIZATION]
        return CommentSummarizerAgent(
            context_service=context_service, comments=comments, llm_handler=llm_handler, model=model
        )
