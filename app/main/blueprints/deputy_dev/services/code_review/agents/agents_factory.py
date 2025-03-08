from typing import Any, Dict, List, Union

from deputydev_core.utils.app_logger import AppLogger

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
                            **agent_type_and_init_params.init_params,
                        )
                    )

        return initialized_agents

    # async def build_prompts(self, reflection_stage, previous_review_comments, exclude_agents):
    #     prompts = await self.build_code_review_agents_prompt(reflection_stage, previous_review_comments, exclude_agents)
    #     prompt = await self.build_pr_summary_prompt(reflection_stage, previous_review_comments, exclude_agents)
    #     if prompt:
    #         prompts[AgentTypes.PR_SUMMARY.value] = prompt

    #     meta_info = {
    #         "issue_id": self.context_service.issue_id,
    #         "confluence_doc_id": self.context_service.confluence_id,
    #     }
    #     return prompts, meta_info

    # async def build_pr_summary_prompt(self, reflection_stage, previous_review_comments, exclude_agents):
    #     agent = AgentTypes.PR_SUMMARY.value
    #     _klass = self.factories[agent]
    #     prompt = await self.__build_prompts(agent, _klass, reflection_stage, previous_review_comments, exclude_agents)
    #     return prompt

    # async def build_code_review_agents_prompt(self, reflection_stage, previous_review_comments, exclude_agents):
    #     prompts = {}
    #     for agent in SettingService.Helper.agents_settings().keys():
    #         predefined_name = SettingService.Helper.custom_name_to_predefined_name(agent)
    #         _klass = self.factories.get(predefined_name)
    #         prompt = await self.__build_prompts(
    #             agent, _klass, reflection_stage, previous_review_comments, exclude_agents
    #         )
    #         if prompt:
    #             prompts[agent] = prompt
    #     return prompts

    # async def __build_prompts(self, agent, agent_class, reflection_stage, previous_review_comments, exclude_agents):
    #     if not agent_class or agent in exclude_agents:
    #         return

    #     agent_instance = agent_class(self.context_service, self.reflection_enabled)
    #     agent_callable = await agent_instance.should_execute()
    #     if not agent_callable:
    #         return

    #     prompt = await agent_instance.get_system_n_user_prompt(
    #         reflection_stage, previous_review_comments.get(agent, {}).get("response")
    #     )
    #     return prompt
