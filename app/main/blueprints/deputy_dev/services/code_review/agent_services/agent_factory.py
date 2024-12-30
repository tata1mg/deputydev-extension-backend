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
from app.main.blueprints.deputy_dev.services.workspace.context_vars import (
    get_context_value,
)
from app.main.blueprints.deputy_dev.services.code_review.agent_services.agent_base import (
    AgentServiceBase,
)
from app.main.blueprints.deputy_dev.constants.constants import TokenTypes
from copy import deepcopy


class AgentFactory:
    FACTORIES = {
        AgentTypes.SECURITY.value: AnthropicSecurityAgent,
        AgentTypes.CODE_COMMUNICATION.value: AnthropicPerformanceOptimisationAgent,
        AgentTypes.PERFORMANCE_OPTIMISATION.value: AnthropicCodeCommunicationAgent,
        AgentTypes.CODE_MAINTAINABILITY.value: AnthropicCodeMaintainabilityAgent,
        AgentTypes.ERROR.value: AnthropicErrorAgent,
        AgentTypes.BUSINESS_LOGIC_VALIDATION.value: AnthropicBusinessValidationAgent,
        AgentTypes.PR_SUMMARY.value: OpenAIPRSummaryAgent,
    }

    def __init__(self, reflection_enabled: bool, context_service: ContextService):
        self.context_service = context_service
        self.reflection_enabled = reflection_enabled
        self.factories = deepcopy(self.FACTORIES)
        self.initialize_custom_agents()

    async def build_prompts(self, reflection_stage, previous_review_comments, exclude_agents):
        prompts = {}
        for agent in AgentTypes.list():

            _klass = self.FACTORIES.get(agent)
            if not _klass or agent in exclude_agents:
                continue

            agent_instance = _klass(self.context_service, self.reflection_enabled)
            agent_callable = await agent_instance.should_execute()
            if not agent_callable:
                continue

            prompts[agent] = await agent_instance.get_system_n_user_prompt(
                reflection_stage, previous_review_comments.get(agent, {}).get("response")
            )

        meta_info = {
            "issue_id": self.context_service.issue_id,
            "confluence_doc_id": self.context_service.confluence_id,
        }
        return prompts, meta_info

    def initialize_custom_agents(self):
        all_agents = get_context_value("setting")["code_review_agents"]["agents"]
        for agent_name, agent_setting in all_agents.items():
            if agent_setting["is_custom_agent"] and agent_setting["enable"]:
                agent_class = self.create_custom_agent(agent_name, self.context_service, self.reflection_enabled)
                self.factories[agent_name] = agent_class

    def create_custom_agent(self, agent_name, context_service, is_reflection_enabled):
        def init_method(self, *args, **kwargs):
            super().__init__(context_service, is_reflection_enabled, agent_name)

        def get_with_reflection_system_prompt_pass1(self):
            return ""

        def get_with_reflection_user_prompt_pass1(self):
            return ""

        def get_with_reflection_system_prompt_pass2(self):
            return ""

        def get_with_reflection_user_prompt_pass2(self):
            return ""

        def get_agent_specific_tokens_data(self):
            return {
                TokenTypes.PR_TITLE.value: self.context_service.pr_title_tokens,
                TokenTypes.PR_DESCRIPTION.value: self.context_service.pr_description_tokens,
                TokenTypes.PR_DIFF_TOKENS.value: self.context_service.pr_diff_tokens[self.agent_id],
                TokenTypes.RELEVANT_CHUNK.value: self.context_service.embedding_input_tokens,
            }

        functions = {
            "__init__": init_method,
            "get_with_reflection_system_prompt_pass1": get_with_reflection_system_prompt_pass1,
            "get_with_reflection_user_prompt_pass1": get_with_reflection_user_prompt_pass1,
            "get_with_reflection_system_prompt_pass2": get_with_reflection_system_prompt_pass2,
            "get_with_reflection_user_prompt_pass2": get_with_reflection_user_prompt_pass2,
            "get_agent_specific_tokens_data": get_agent_specific_tokens_data,
        }
        # Dynamically create and return the class
        return type(agent_name, (AgentServiceBase,), functions)
