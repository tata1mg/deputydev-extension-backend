from copy import deepcopy

from app.main.blueprints.deputy_dev.constants.constants import AgentTypes
from app.main.blueprints.deputy_dev.services.code_review.agent_services.anthropic.anthropic_business_validation_agent import (
    AnthropicBusinessValidationAgent,
)
from app.main.blueprints.deputy_dev.services.code_review.agent_services.anthropic.anthropic_code_communication_agent import (
    AnthropicCodeCommunicationAgent,
)
from app.main.blueprints.deputy_dev.services.code_review.agent_services.anthropic.anthropic_code_maintainability_agent import (
    AnthropicCodeMaintainabilityAgent,
)
from app.main.blueprints.deputy_dev.services.code_review.agent_services.anthropic.anthropic_custom_agent import (
    AnthropicCustomAgent,
)
from app.main.blueprints.deputy_dev.services.code_review.agent_services.anthropic.anthropic_error_agent import (
    AnthropicErrorAgent,
)
from app.main.blueprints.deputy_dev.services.code_review.agent_services.anthropic.anthropic_performance_optimisation_agent import (
    AnthropicPerformanceOptimisationAgent,
)
from app.main.blueprints.deputy_dev.services.code_review.agent_services.anthropic.anthropic_security_agent import (
    AnthropicSecurityAgent,
)
from app.main.blueprints.deputy_dev.services.code_review.agent_services.openai.openai_summary_agent import (
    OpenAIPRSummaryAgent,
)
from app.main.blueprints.deputy_dev.services.code_review.context.context_service import (
    ContextService,
)
from app.main.blueprints.deputy_dev.services.setting.setting_service import (
    SettingService,
)


class AgentFactory:
    FACTORIES = {
        AgentTypes.SECURITY.value: AnthropicSecurityAgent,
        AgentTypes.CODE_COMMUNICATION.value: AnthropicCodeCommunicationAgent,
        AgentTypes.PERFORMANCE_OPTIMISATION.value: AnthropicPerformanceOptimisationAgent,
        AgentTypes.CODE_MAINTAINABILITY.value: AnthropicCodeMaintainabilityAgent,
        AgentTypes.ERROR.value: AnthropicErrorAgent,
        AgentTypes.BUSINESS_LOGIC_VALIDATION.value: AnthropicBusinessValidationAgent,
        AgentTypes.PR_SUMMARY.value: OpenAIPRSummaryAgent,
    }

    def __init__(self, reflection_enabled: bool, context_service: ContextService, include_agents: list = None):
        self.context_service = context_service
        self.reflection_enabled = reflection_enabled
        self.include_agents = include_agents
        self.factories = {}
        self.initialize_factories()
        self.initialize_anthropic_custom_agents()

    # Concept of include_agents and exclude_agents:
    # If only include_agents is provided, self.factories will contain only the agents
    # specified in include_agents, and prompts will only be built for those agents.
    #
    # If only exclude_agents is provided, self.factories will contain all the default agents.
    # However, while building prompts for each agent, the agents specified in exclude_agents
    # will be excluded from the prompt generation.
    #
    # If both include_agents and exclude_agents are provided, self.factories will first be built
    # based on include_agents. Then, while building prompts, the agents specified in exclude_agents
    # will be excluded from the agents in self.factories.

    def initialize_factories(self):
        """Initialize factories based on include_agents filter."""
        if self.include_agents:
            self.factories = {agent: self.FACTORIES[agent] for agent in self.include_agents if agent in self.FACTORIES}
        else:
            self.factories = deepcopy(self.FACTORIES)

    async def build_prompts(self, reflection_stage, previous_review_comments, exclude_agents):
        prompts = await self.build_code_review_agents_prompt(reflection_stage, previous_review_comments, exclude_agents)
        prompt = await self.build_pr_summary_prompt(reflection_stage, previous_review_comments, exclude_agents)
        if prompt:
            prompts[AgentTypes.PR_SUMMARY.value] = prompt

        meta_info = {
            "issue_id": self.context_service.issue_id,
            "confluence_doc_id": self.context_service.confluence_id,
        }
        return prompts, meta_info

    async def build_pr_summary_prompt(self, reflection_stage, previous_review_comments, exclude_agents):
        agent = AgentTypes.PR_SUMMARY.value
        _klass = self.factories[agent]
        prompt = await self.__build_prompts(agent, _klass, reflection_stage, previous_review_comments, exclude_agents)
        return prompt

    async def build_code_review_agents_prompt(self, reflection_stage, previous_review_comments, exclude_agents):
        prompts = {}
        for agent in SettingService.Helper.agents_settings().keys():
            predefined_name = SettingService.Helper.custom_name_to_predefined_name(agent)
            _klass = self.factories.get(predefined_name)
            prompt = await self.__build_prompts(
                agent, _klass, reflection_stage, previous_review_comments, exclude_agents
            )
            if prompt:
                prompts[agent] = prompt
        return prompts

    async def __build_prompts(self, agent, agent_class, reflection_stage, previous_review_comments, exclude_agents):
        if not agent_class or agent in exclude_agents:
            return

        agent_instance = agent_class(self.context_service, self.reflection_enabled)
        agent_callable = await agent_instance.should_execute()
        if not agent_callable:
            return

        prompt = await agent_instance.get_system_n_user_prompt(
            reflection_stage, previous_review_comments.get(agent, {}).get("response")
        )
        return prompt

    def initialize_anthropic_custom_agents(self):
        for agent_name, agent_setting in SettingService.Helper.agents_settings().items():
            if agent_setting["is_custom_agent"] and agent_setting["enable"]:
                # For cases where include_agents is passed then only include those custom agent if they are part of include_agents list
                if not self.include_agents or (self.include_agents and agent_name in self.include_agents):
                    agent_class = AnthropicCustomAgent.create_custom_agent(
                        agent_name, self.context_service, self.reflection_enabled
                    )
                    self.factories[agent_name] = agent_class
