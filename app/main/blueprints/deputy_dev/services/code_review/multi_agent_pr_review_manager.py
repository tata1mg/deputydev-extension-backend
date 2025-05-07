import asyncio
from typing import Any, Dict, List, Optional, Tuple

from deputydev_core.services.tiktoken import TikToken
from deputydev_core.utils.config_manager import ConfigManager

from app.backend_common.services.llm.dataclasses.main import PromptCacheConfig
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
    AgentRunResult,
    AgentTypes,
)
from app.main.blueprints.deputy_dev.services.code_review.comments.comment_blending_engine import (
    CommentBlendingEngine,
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


class MultiAgentPRReviewManager:
    def __init__(
        self,
        repo_service: BaseRepo,
        pr_service: BasePR,
        pr_diff_handler: PRDiffHandler,
        session_id: int,
        prompt_version=None,
        eligible_agents=None,
    ):
        self.repo_service = repo_service
        self.pr_service = pr_service
        self.multi_agent_enabled = None
        self.reflection_enabled = None
        self.pr_diff = None
        self.contexts = None
        self.agent_results: Dict[str, AgentRunResult] = {}
        self.blending_agent_results: Dict[str, AgentRunResult] = {}
        self.multi_agent_reflection_stage = MultiAgentReflectionIteration.PASS_1.value
        self.tokens_data = {}
        self.meta_info_to_save = {}
        self.prompt_version = prompt_version
        self.tiktoken = TikToken()
        self.agents_tokens = {}
        self.filtered_comments = None
        self.pr_summary: Optional[Dict[str, Any]] = None
        self.pr_summary_tokens = {}
        self.context_service = ContextService(repo_service, pr_service, pr_diff_handler=pr_diff_handler)
        self.eligible_agents = eligible_agents
        self._is_large_pr: bool = False
        self.pr_diff_handler = pr_diff_handler
        self.llm_handler = LLMHandler(
            prompt_factory=PromptFeatureFactory,
            prompt_features=PromptFeatures,
            cache_config=PromptCacheConfig(conversation=True, tools=True, system_message=True),
        )
        self.session_id = session_id

    # section setting start

    def _is_reflection_enabled(self) -> bool:
        if self.reflection_enabled is None:
            self.reflection_enabled = ConfigManager.configs["PR_REVIEW_SETTINGS"]["REFLECTION_ENABLED"]
        return self.reflection_enabled

    # blending engine section start
    async def filter_comments(self):
        if not self.agent_results:
            return
        self.filtered_comments, self.blending_agent_results = await CommentBlendingEngine(
            self.agent_results, self.context_service, self.llm_handler, self.session_id
        ).blend_comments()

    # blending engine section end

    def populate_pr_summary(self):
        pr_summary = self.agent_results.pop(AgentTypes.PR_SUMMARY.value, None)
        self.pr_summary = pr_summary.agent_result if pr_summary else None
        self.pr_summary_tokens = pr_summary.tokens_data if pr_summary else {}

    def populate_meta_info(self):
        self.agents_tokens.update(self.pr_summary_tokens)
        for agent, agent_run_results in self.agent_results.items():
            self.agents_tokens.update(agent_run_results.tokens_data)

    async def return_final_response(
        self,
    ) -> Tuple[Optional[List[Dict[str, Any]]], str, Dict[str, Any], Dict[str, Any], bool]:
        formatted_summary = ""
        if self.pr_summary:
            loc = await self.pr_service.get_loc_changed_count()
            formatted_summary = format_summary_with_metadata(
                summary=self.pr_summary, loc=loc, commit_id=self.pr_service.pr_model().commit_id()
            )
        return (
            [comment.model_dump(mode="json") for comment in self.filtered_comments] if self.filtered_comments else None,
            formatted_summary,
            self.agents_tokens,
            {
                "issue_id": self.context_service.issue_id,
                "confluence_doc_id": self.context_service.confluence_id,
            },
            self._is_large_pr,
        )

    async def get_code_review_comments(
        self,
    ) -> Tuple[Optional[List[Dict[str, Any]]], str, Dict[str, Any], Dict[str, Any], bool]:
        # get all agents from factory
        all_agents = AgentFactory.get_code_review_agents(
            context_service=self.context_service,
            is_reflection_enabled=self._is_reflection_enabled(),
            llm_handler=self.llm_handler,
        )

        # segregate agents in realtime based on whether they should execute or not
        runnable_agents = [agent for agent in all_agents if await agent.should_execute()]
        agent_tasks = [agent.run_agent(session_id=self.session_id) for agent in runnable_agents]
        agent_tasks_results = await asyncio.gather(*agent_tasks, return_exceptions=False)
        non_error_results = [
            task_result for task_result in agent_tasks_results if not isinstance(task_result, BaseException)
        ]
        self._is_large_pr = all([agent_result.prompt_tokens_exceeded for agent_result in non_error_results])

        # TODO: Remoove this, same variable should not be used for two different purposes
        if self._is_large_pr:
            self.agents_tokens = await self.pr_diff_handler.get_pr_diff_token_count()

        # set self.llm_comments
        for agent_result in non_error_results:
            if agent_result.agent_result is not None:
                if agent_result.agent_type != AgentTypes.PR_SUMMARY:
                    self.update_bucket_name(agent_result)
                self.agent_results[agent_result.agent_name] = agent_result

        self.populate_pr_summary()
        await self.filter_comments()
        self.agent_results.update(self.blending_agent_results)
        self.populate_meta_info()
        return await self.return_final_response()

    def update_bucket_name(self, agent_result: AgentRunResult):
        comments = agent_result.agent_result["comments"]
        for comment in comments:
            display_name = agent_result.display_name
            comment.bucket = "_".join(display_name.upper().split())
