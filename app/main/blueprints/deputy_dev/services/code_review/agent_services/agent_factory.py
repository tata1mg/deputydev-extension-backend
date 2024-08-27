from app.main.blueprints.deputy_dev.constants.constants import AgentTypes
from app.main.blueprints.deputy_dev.services.code_review.agent_services.anthropic.anthropic_business_validation_agent import (
    AnthropicBusinessValidationAgent,
)
from app.main.blueprints.deputy_dev.services.code_review.agent_services.anthropic.anthropic_code_communication_agent import \
    AnthropicCodeCommunicationAgent
from app.main.blueprints.deputy_dev.services.code_review.agent_services.anthropic.anthropic_code_maintainability_agent import (
    AnthropicCodeMaintainabilityAgent,
)
from app.main.blueprints.deputy_dev.services.code_review.agent_services.anthropic.anthropic_error_agent import (
    AnthropicErrorAgent,
)
from app.main.blueprints.deputy_dev.services.code_review.agent_services.anthropic.anthropic_performance_optimisation_agent import \
    AnthropicPerformanceOptimisationAgent
from app.main.blueprints.deputy_dev.services.code_review.agent_services.anthropic.anthropic_security_agent import \
    AnthropicSecurityAgent
from app.main.blueprints.deputy_dev.services.code_review.agent_services.openai.openai_summary_agent import (
    OpenAIPRSummaryAgent,
)
from app.main.blueprints.deputy_dev.services.code_review.context.context_service import (
    ContextService,
)
from app.main.blueprints.deputy_dev.services.repo.base_repo import BaseRepo


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

    def __init__(self, repo_service: BaseRepo, reflection_enabled: bool):
        self.context_service = ContextService(repo_service)
        self.reflection_enabled = reflection_enabled

    async def build_prompts(self, reflection_stage, previous_review_comments, exclude_agents):
        prompts = {}
        for agent in AgentTypes.list():
            _klass = self.FACTORIES.get(agent)
            if _klass and agent not in exclude_agents:
                prompts[agent] = await _klass(self.context_service, self.reflection_enabled).get_system_n_user_prompt(
                    reflection_stage, previous_review_comments.get(agent, {}).get("response")
                )
        meta_info = {
            "issue_id": self.context_service.issue_id,
            "confluence_doc_id": self.context_service.confluence_id,
        }
        return prompts, meta_info
