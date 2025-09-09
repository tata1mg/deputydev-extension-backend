from typing import List, Union

from app.main.blueprints.deputy_dev.services.code_review.common.agents.dataclasses.main import (
    AgentAndInitParams,
    AgentTypes,
)
from app.main.blueprints.deputy_dev.services.code_review.common.comments.dataclasses.main import (
    ParsedAggregatedCommentData,
    ParsedCommentData,
)
from app.main.blueprints.deputy_dev.services.code_review.common.prompts.dataclasses.main import (
    PromptFeatures,
)
from app.main.blueprints.deputy_dev.services.code_review.vcs_review.agents.base_code_review_agent import (
    BaseCodeReviewAgent,
)
from app.main.blueprints.deputy_dev.services.code_review.vcs_review.agents.llm_agents.comment_summarizer.comment_summarizer_agent import (
    CommentSummarizerAgent,
)
from app.main.blueprints.deputy_dev.services.code_review.vcs_review.agents.llm_agents.comment_validator.comment_validator_agent import (
    CommentValidatorAgent,
)
from app.main.blueprints.deputy_dev.services.code_review.vcs_review.agents.llm_agents.commenters.commenter_agents.business_validation_agent import (
    BusinessValidationAgent,
)
from app.main.blueprints.deputy_dev.services.code_review.vcs_review.agents.llm_agents.commenters.commenter_agents.code_communication_agent import (
    CodeCommunicationAgent,
)
from app.main.blueprints.deputy_dev.services.code_review.vcs_review.agents.llm_agents.commenters.commenter_agents.code_maintainability_agent import (
    CodeMaintainabilityAgent,
)
from app.main.blueprints.deputy_dev.services.code_review.vcs_review.agents.llm_agents.commenters.commenter_agents.error_agent import (
    ErrorAgent,
)
from app.main.blueprints.deputy_dev.services.code_review.vcs_review.agents.llm_agents.commenters.commenter_agents.performance_optimization_agent import (
    PerformanceOptimizationAgent,
)
from app.main.blueprints.deputy_dev.services.code_review.vcs_review.agents.llm_agents.commenters.commenter_agents.security_agent import (
    SecurityAgent,
)
from app.main.blueprints.deputy_dev.services.code_review.vcs_review.context.context_service import (
    ContextService,
)
from deputydev_core.llm_handler.core.handler import LLMHandler
from deputydev_core.llm_handler.models.dto.message_thread_dto import LLModels


class AgentFactory:
    agent_type_to_model_map = {
        AgentTypes.BUSINESS_LOGIC_VALIDATION: LLModels.CLAUDE_4_SONNET,
        AgentTypes.CODE_MAINTAINABILITY: LLModels.CLAUDE_4_SONNET,
        AgentTypes.CODE_COMMUNICATION: LLModels.CLAUDE_4_SONNET,
        AgentTypes.ERROR: LLModels.CLAUDE_4_SONNET,
        AgentTypes.PERFORMANCE_OPTIMIZATION: LLModels.CLAUDE_4_SONNET,
        AgentTypes.SECURITY: LLModels.CLAUDE_4_SONNET,
        AgentTypes.PR_SUMMARY: LLModels.GPT_4_POINT_1,
        AgentTypes.COMMENT_VALIDATION: LLModels.GPT_4_POINT_1,
        AgentTypes.COMMENT_SUMMARIZATION: LLModels.GPT_4_POINT_1,
        AgentTypes.CUSTOM_COMMENTER_AGENT: LLModels.CLAUDE_4_SONNET,
    }

    code_review_agents = {
        AgentTypes.BUSINESS_LOGIC_VALIDATION: BusinessValidationAgent,
        AgentTypes.CODE_MAINTAINABILITY: CodeMaintainabilityAgent,
        AgentTypes.CODE_COMMUNICATION: CodeCommunicationAgent,
        AgentTypes.ERROR: ErrorAgent,
        AgentTypes.PERFORMANCE_OPTIMIZATION: PerformanceOptimizationAgent,
        AgentTypes.SECURITY: SecurityAgent,
        # AgentTypes.PR_SUMMARY: PRSummarizerAgent,
        # AgentTypes.CUSTOM_COMMENTER_AGENT: CustomAgent,
    }

    review_finalization_agents = {
        AgentTypes.COMMENT_VALIDATION: CommentValidatorAgent,
        AgentTypes.COMMENT_SUMMARIZATION: CommentSummarizerAgent,
    }

    @classmethod
    def get_code_review_agents(
        cls,
        valid_agents_and_init_params: List[AgentAndInitParams],
        context_service: ContextService,
        llm_handler: LLMHandler[PromptFeatures],
        is_reflection_enabled: bool = True,
        include_agent_types: List[AgentTypes] = [],
        exclude_agent_types: List[AgentTypes] = [],
    ) -> List[BaseCodeReviewAgent]:
        initialized_agents: List[BaseCodeReviewAgent] = []

        for agent_type_and_init_params in valid_agents_and_init_params:
            if not include_agent_types or agent_type_and_init_params.agent_type in include_agent_types:
                if cls.code_review_agents.get(agent_type_and_init_params.agent_type) and (
                    not exclude_agent_types or agent_type_and_init_params.agent_type not in exclude_agent_types
                ):
                    initialized_agents.append(
                        cls.code_review_agents[agent_type_and_init_params.agent_type](
                            context_service=context_service,
                            is_reflection_enabled=is_reflection_enabled,
                            llm_handler=llm_handler,
                            model=cls.agent_type_to_model_map[agent_type_and_init_params.agent_type],
                            **agent_type_and_init_params.init_params,
                        )
                    )

        return initialized_agents

    @classmethod
    def get_review_finalization_agents(
        cls,
        context_service: ContextService,
        comments: Union[List[ParsedCommentData], List[ParsedAggregatedCommentData]],
        llm_handler: LLMHandler[PromptFeatures],
        is_reflection_enabled: bool = True,
        include_agent_types: List[AgentTypes] = [],
        exclude_agent_types: List[AgentTypes] = [],
    ) -> List[BaseCodeReviewAgent]:
        initialized_agents: List[BaseCodeReviewAgent] = []
        for agent_type, agent_class in cls.review_finalization_agents.items():
            if not include_agent_types or agent_type in include_agent_types:
                if not exclude_agent_types or agent_type not in exclude_agent_types:
                    initialized_agents.append(
                        agent_class(
                            context_service=context_service,
                            is_reflection_enabled=is_reflection_enabled,
                            llm_handler=llm_handler,
                            model=cls.agent_type_to_model_map[agent_type],
                            agent_setting={},
                            comments=comments,
                        )
                    )

        return initialized_agents
