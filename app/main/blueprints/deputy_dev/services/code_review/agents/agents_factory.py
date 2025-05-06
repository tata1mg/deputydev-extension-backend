from typing import List, Union

from deputydev_core.utils.app_logger import AppLogger
from deputydev_core.utils.config_manager import ConfigManager

from app.backend_common.models.dto.message_thread_dto import LLModels
from app.backend_common.services.llm.handler import LLMHandler
from app.main.blueprints.deputy_dev.services.code_review.agents.base_code_review_agent import (
    BaseCodeReviewAgent,
)
from app.main.blueprints.deputy_dev.services.code_review.agents.dataclasses.main import (
    AgentAndInitParams,
    AgentTypes,
)
from app.main.blueprints.deputy_dev.services.code_review.agents.llm_agents.comment_summarizer.comment_summarizer_agent import (
    CommentSummarizerAgent,
)
from app.main.blueprints.deputy_dev.services.code_review.agents.llm_agents.comment_validator.comment_validator_agent import (
    CommentValidatorAgent,
)
from app.main.blueprints.deputy_dev.services.code_review.agents.llm_agents.commenters.commenter_agents.business_validation_agent import (
    BusinessValidationAgent,
)
from app.main.blueprints.deputy_dev.services.code_review.agents.llm_agents.commenters.commenter_agents.code_communication_agent import (
    CodeCommunicationAgent,
)
from app.main.blueprints.deputy_dev.services.code_review.agents.llm_agents.commenters.commenter_agents.code_maintainability_agent import (
    CodeMaintainabilityAgent,
)
from app.main.blueprints.deputy_dev.services.code_review.agents.llm_agents.commenters.commenter_agents.error_agent import (
    ErrorAgent,
)
from app.main.blueprints.deputy_dev.services.code_review.agents.llm_agents.commenters.commenter_agents.performance_optimization_agent import (
    PerformanceOptimizationAgent,
)
from app.main.blueprints.deputy_dev.services.code_review.agents.llm_agents.commenters.commenter_agents.security_agent import (
    SecurityAgent,
)
from app.main.blueprints.deputy_dev.services.code_review.agents.llm_agents.pr_summarizer.pr_summarizer_agent import (
    PRSummarizerAgent,
)
from app.main.blueprints.deputy_dev.services.code_review.comments.dataclasses.main import (
    ParsedAggregatedCommentData,
    ParsedCommentData,
)
from app.main.blueprints.deputy_dev.services.code_review.context.context_service import (
    ContextService,
)
from app.main.blueprints.deputy_dev.services.code_review.prompts.dataclasses.main import (
    PromptFeatures,
)
from app.main.blueprints.deputy_dev.services.setting.setting_service import (
    SettingService,
)


class AgentFactory:
    agent_type_to_model_map = {
        AgentTypes.BUSINESS_LOGIC_VALIDATION: LLModels.CLAUDE_3_POINT_7_SONNET,
        AgentTypes.CODE_MAINTAINABILITY: LLModels.CLAUDE_3_POINT_7_SONNET,
        AgentTypes.CODE_COMMUNICATION: LLModels.CLAUDE_3_POINT_7_SONNET,
        AgentTypes.ERROR: LLModels.CLAUDE_3_POINT_7_SONNET,
        AgentTypes.PERFORMANCE_OPTIMIZATION: LLModels.CLAUDE_3_POINT_7_SONNET,
        AgentTypes.SECURITY: LLModels.CLAUDE_3_POINT_7_SONNET,
        AgentTypes.PR_SUMMARY: LLModels.GPT_4O,
        AgentTypes.COMMENT_VALIDATION: LLModels.GPT_4O,
        AgentTypes.COMMENT_SUMMARIZATION: LLModels.GPT_4O,
    }

    code_review_agents = {
        AgentTypes.BUSINESS_LOGIC_VALIDATION: BusinessValidationAgent,
        AgentTypes.CODE_MAINTAINABILITY: CodeMaintainabilityAgent,
        AgentTypes.CODE_COMMUNICATION: CodeCommunicationAgent,
        AgentTypes.ERROR: ErrorAgent,
        AgentTypes.PERFORMANCE_OPTIMIZATION: PerformanceOptimizationAgent,
        AgentTypes.SECURITY: SecurityAgent,
        AgentTypes.PR_SUMMARY: PRSummarizerAgent,
    }

    review_finalization_agents = {
        AgentTypes.COMMENT_VALIDATION: CommentValidatorAgent,
        AgentTypes.COMMENT_SUMMARIZATION: CommentSummarizerAgent,
    }

    @classmethod
    def get_valid_agents_and_init_params_for_review(
        cls,
    ) -> List[AgentAndInitParams]:

        valid_agents: List[AgentAndInitParams] = []

        # add predefined and custom code commenter agents
        code_review_agent_rules = SettingService.helper.global_code_review_agent_rules()
        if code_review_agent_rules.get("enable"):
            agent_settings = SettingService.helper.agents_settings()
            for agent_name, agent_setting in agent_settings.items():
                if agent_setting["enable"]:
                    if agent_setting["is_custom_agent"]:
                        valid_agents.append(
                            AgentAndInitParams(
                                agent_type=AgentTypes.CUSTOM_COMMENTER_AGENT,
                                init_params={"custom_commenter_name": agent_name},
                            )
                        )
                    else:
                        try:
                            agent_name = AgentTypes(agent_name)
                            valid_agents.append(AgentAndInitParams(agent_type=agent_name))
                        except ValueError:
                            AppLogger.log_warn(f"Invalid agent name: {agent_name}")

        # add code summarization agent
        summary_agent_setting = SettingService.helper.summary_agent_setting()
        if summary_agent_setting.get("enable"):
            valid_agents.append(AgentAndInitParams(agent_type=AgentTypes.PR_SUMMARY))

        return valid_agents

    @classmethod
    def get_code_review_agents(
        cls,
        context_service: ContextService,
        llm_handler: LLMHandler[PromptFeatures],
        is_reflection_enabled: bool = True,
        include_agent_types: List[AgentTypes] = [],
        exclude_agent_types: List[AgentTypes] = [],
    ) -> List[BaseCodeReviewAgent]:
        valid_agents_and_init_params = cls.get_valid_agents_and_init_params_for_review()

        initialized_agents: List[BaseCodeReviewAgent] = []

        for agent_type_and_init_params in valid_agents_and_init_params:
            if not include_agent_types or agent_type_and_init_params.agent_type in include_agent_types:
                if not exclude_agent_types or agent_type_and_init_params.agent_type not in exclude_agent_types:
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
