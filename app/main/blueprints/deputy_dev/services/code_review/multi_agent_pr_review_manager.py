import asyncio

from deputydev_core.services.tiktoken import TikToken
from torpedo import CONFIG

from app.backend_common.services.llm.handler import LLMHandler
from app.backend_common.services.pr.base_pr import BasePR
from app.backend_common.services.repo.base_repo import BaseRepo
from app.backend_common.utils.formatting import format_summary_with_metadata
from app.main.blueprints.deputy_dev.constants.constants import (
    MultiAgentReflectionIteration,
)
from app.main.blueprints.deputy_dev.helpers.pr_diff_handler import PRDiffHandler
from app.main.blueprints.deputy_dev.services.code_review.agents.agents_factory import (
    AgentFactory,
)
from app.main.blueprints.deputy_dev.services.code_review.agents.dataclasses.main import (
    AgentTypes,
)
from app.main.blueprints.deputy_dev.services.code_review.context.context_service import (
    ContextService,
)
from app.main.blueprints.deputy_dev.services.code_review.prompts.dataclasses.main import (
    PromptFeatures,
)
from app.main.blueprints.deputy_dev.services.code_review.prompts.factory import (
    PromptFeatureFactory,
)
from app.main.blueprints.deputy_dev.services.comment.comment_blending_engine import (
    CommentBlendingEngine,
)


class MultiAgentPRReviewManager:
    def __init__(
        self,
        repo_service: BaseRepo,
        pr_service: BasePR,
        pr_diff_handler: PRDiffHandler,
        prompt_version=None,
        eligible_agents=None,
        session_id: int = None,
    ):
        self.repo_service = repo_service
        self.pr_service = pr_service
        self.multi_agent_enabled = None
        self.reflection_enabled = None
        self.pr_diff = None
        self.contexts = None
        self.current_prompts = None
        self.llm_comments = {}
        self.multi_agent_reflection_stage = MultiAgentReflectionIteration.PASS_1.value
        self.tokens_data = {}
        self.meta_info_to_save = {}
        self.prompt_version = prompt_version
        self.tiktoken = TikToken()
        self.agents_tokens = {}
        self.filtered_comments = None
        self.pr_summary = None
        self.exclude_agent = set()
        self.context_service = ContextService(repo_service, pr_service, pr_diff_handler=pr_diff_handler)
        self.eligible_agents = eligible_agents
        self.agent_factory = AgentFactory(
            reflection_enabled=self._is_reflection_enabled(),
            context_service=self.context_service,
            eligible_agents=self.eligible_agents,
        )
        self._is_large_pr = False
        self.pr_diff_handler = pr_diff_handler
        self.llm_handler = LLMHandler(
            prompt_factory=PromptFeatureFactory,
            prompt_features=PromptFeatures,
        )
        self.session_id = session_id

    # section setting start

    def _is_reflection_enabled(self) -> bool:
        if self.reflection_enabled is None:
            self.reflection_enabled = CONFIG.config["PR_REVIEW_SETTINGS"]["REFLECTION_ENABLED"]
        return self.reflection_enabled

    # blending engine section start
    async def filter_comments(self):
        if not self.llm_comments:
            return
        self.filtered_comments = await CommentBlendingEngine(self.llm_comments, self.context_service).blend_comments()

    # blending engine section end

    def populate_pr_summary(self):
        self.pr_summary = self.llm_comments.pop(AgentTypes.PR_SUMMARY.value, "")

    def all_prompts_exceed_token_limit(self):
        all_exceeded = True

        for prompt, prompt_data in self.current_prompts.items():
            if prompt_data["exceeds_tokens"]:
                self.exclude_agent.add(prompt)
            else:
                all_exceeded = False

        self._is_large_pr = all_exceeded
        if all_exceeded:
            self.llm_comments = {}
            pr_diff_tokens_count = await self.pr_diff_handler.get_pr_diff_token_count()
            self.agents_tokens = pr_diff_tokens_count

    def populate_meta_info(self):
        for agent, prompt in self.current_prompts.items():
            agent_identifier = prompt["key"] + prompt["reflection_iteration"]
            self.agents_tokens[agent_identifier] = prompt.pop("tokens")
            self.agents_tokens[agent_identifier].update(
                {
                    "input_tokens": self.llm_comments.get(agent, {}).get("input_tokens", 0),
                    "output_tokens": self.llm_comments.get(agent, {}).get("output_tokens", 0),
                }
            )

    async def return_final_response(self):
        formatted_summary = ""
        if self.pr_summary and isinstance(self.pr_summary, dict) and self.pr_summary.get("response"):
            loc = await self.pr_service.get_loc_changed_count()
            formatted_summary = await format_summary_with_metadata(
                summary=self.pr_summary["response"], loc=loc, commit_id=self.pr_service.pr_model().commit_id()
            )
        return (
            self.filtered_comments,
            formatted_summary,
            self.agents_tokens,
            {
                "issue_id": self.context_service.issue_id,
                "confluence_doc_id": self.context_service.confluence_id,
            },
            self._is_large_pr,
        )

    async def get_code_review_comments(self):
        # get all agents from factory
        all_agents = AgentFactory.get_agents(
            context_service=self.context_service,
            is_reflection_enabled=self._is_reflection_enabled(),
            llm_handler=self.llm_handler,
        )

        # segregate agents in realtime based on whether they should execute or not
        runnable_agents = [agent for agent in all_agents if await agent.should_execute()]
        agent_tasks = [agent.run_agent(session_id=self.session_id) for agent in runnable_agents]
        agent_tasks_results = await asyncio.gather(*agent_tasks, return_exceptions=True)
        self.populate_pr_summary()
        self.populate_meta_info()
        await self.filter_comments()
        return await self.return_final_response()
