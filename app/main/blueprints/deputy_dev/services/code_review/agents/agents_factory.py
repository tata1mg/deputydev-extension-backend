from enum import Enum
from typing import List

from deputydev_core.utils.app_logger import AppLogger
from deputydev_core.utils.config_manager import ConfigManager
from torpedo import CONFIG

from app.backend_common.models.dto.message_thread_dto import LLModels
from app.backend_common.services.llm.handler import LLMHandler
from app.backend_common.services.llm.prompts.base_prompt_feature_factory import (
    BasePromptFeatureFactory,
)
from app.main.blueprints.deputy_dev.services.code_review.agents.base_code_review_agent import (
    BaseCodeReviewAgent,
)
from app.main.blueprints.deputy_dev.services.code_review.agents.dataclasses.main import (
    AgentAndInitParams,
    AgentTypes,
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
    agents = {
        AgentTypes.BUSINESS_LOGIC_VALIDATION: BusinessValidationAgent,
        AgentTypes.CODE_MAINTAINABILITY: CodeMaintainabilityAgent,
        AgentTypes.CODE_COMMUNICATION: CodeCommunicationAgent,
        AgentTypes.ERROR: ErrorAgent,
        AgentTypes.PERFORMANCE_OPTIMIZATION: PerformanceOptimizationAgent,
        AgentTypes.SECURITY: SecurityAgent,
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
    def get_agents(
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
                        cls.agents[agent_type_and_init_params.agent_type](
                            context_service=context_service,
                            is_reflection_enabled=is_reflection_enabled,
                            llm_handler=llm_handler,
                            model=LLModels(ConfigManager.configs["FEATURE_MODELS"]["PR_REVIEW"])
                            ** agent_type_and_init_params.init_params,
                        )
                    )

        return initialized_agents
