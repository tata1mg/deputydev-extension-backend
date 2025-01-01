import time

from torpedo import CONFIG

from app.common.services.llm.multi_agents_manager import MultiAgentsLLMManager
from app.common.services.pr.base_pr import BasePR
from app.common.services.repo.base_repo import BaseRepo
from app.common.services.tiktoken import TikToken
from app.main.blueprints.deputy_dev.constants.constants import (
    AgentTypes,
    MultiAgentReflectionIteration,
)
from app.main.blueprints.deputy_dev.loggers import AppLogger
from app.main.blueprints.deputy_dev.services.code_review.agent_services.agent_factory import (
    AgentFactory,
)
from app.main.blueprints.deputy_dev.services.code_review.context.context_service import (
    ContextService,
)
from app.main.blueprints.deputy_dev.services.comment.comment_blending_engine import (
    CommentBlendingEngine,
)
from app.main.blueprints.deputy_dev.services.workspace.context_vars import (
    get_context_value,
)


class MultiAgentPRReviewManager:
    def __init__(self, repo_service: BaseRepo, pr_service: BasePR, prompt_version=None):
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
        self.context_service = ContextService(repo_service, pr_service)
        self.agent_factory = AgentFactory(
            reflection_enabled=self._is_reflection_enabled(), context_service=self.context_service
        )
        self._is_large_pr = False

    # section setting start

    def _is_reflection_enabled(self):
        if self.reflection_enabled is None:
            self.reflection_enabled = CONFIG.config["PR_REVIEW_SETTINGS"]["REFLECTION_ENABLED"]
        return self.reflection_enabled

    # section setting end

    # section prompt start

    async def _build_prompts(self):
        self.current_prompts, self.meta_info_to_save = await self.agent_factory.build_prompts(
            reflection_stage=self.multi_agent_reflection_stage,
            previous_review_comments=self.llm_comments,
            exclude_agents=self.exclude_agent,
        )

    async def _build_post_reflection_prompt(self):
        self.exclude_agent.add(AgentTypes.PR_SUMMARY.value)  # Exclude summary in reflection call
        self.multi_agent_reflection_stage = MultiAgentReflectionIteration.PASS_2.value
        await self._build_prompts()

    # section prompt end

    # llm handler start
    async def _make_llm_calls(self):
        contexts = []
        for agent in self.current_prompts:
            if agent not in self.exclude_agent:
                contexts.append(self.current_prompts[agent])
        self.llm_comments = await MultiAgentsLLMManager.get_llm_response(contexts)
        return self.llm_comments

    # llm handler end

    # blending engine section start
    async def filter_comments(self):
        self.filtered_comments = await CommentBlendingEngine(self.llm_comments, self.context_service).blend_comments()

    # blending engine section end

    def populate_pr_summary(self):
        self.pr_summary = self.llm_comments.get(AgentTypes.PR_SUMMARY.value) or ""

    async def __execute_pass(self):
        await self._build_prompts()
        self.all_prompts_exceed_token_limit()
        if self._is_large_pr:
            self.llm_comments = {}
            pr_diff_tokens_count = await self.pr_service.get_pr_diff_token_count()
            self.agents_tokens = {"pr_diff_tokens": pr_diff_tokens_count}
            return
        t1 = time.time() * 1000
        await self._make_llm_calls()
        t2 = time.time() * 1000
        AppLogger.log_info(f"Time taken in LLM call - {t2 - t1} ms")
        self.populate_meta_info()

    def exclude_disabled_agents(self):
        setting = get_context_value("setting")
        for agent, agent_setting in setting["code_review_agent"]["agents"].items():
            if not agent_setting["enable"] or not setting["code_review_agent"]["enable"]:
                self.exclude_agent.add(agent)
        if not setting[AgentTypes.PR_SUMMARY.value]["enable"]:
            self.exclude_agent.add(AgentTypes.PR_SUMMARY.value)

    async def execute_pass_1(self):
        await self.__execute_pass()
        self.populate_pr_summary()

    async def execute_pass_2(self):
        self.exclude_agent.add(AgentTypes.PR_SUMMARY.value)  # Exclude summary in reflection call
        self.multi_agent_reflection_stage = MultiAgentReflectionIteration.PASS_2.value
        await self.__execute_pass()

    async def get_code_review_comments(self):
        self.exclude_disabled_agents()
        await self.execute_pass_1()
        if get_context_value("setting")["code_review_agent"]["enable"]:
            await self.execute_pass_2() if self._is_reflection_enabled() else None
            await self.filter_comments()
        return self.return_final_response()

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

    def return_final_response(self):
        return self.filtered_comments, self.pr_summary, self.agents_tokens, self.meta_info_to_save, self._is_large_pr

    def all_prompts_exceed_token_limit(self):
        all_exceeded = True

        for prompt, prompt_data in self.current_prompts.items():
            if prompt_data["exceeds_tokens"]:
                self.exclude_agent.add(prompt)
            else:
                all_exceeded = False

        self._is_large_pr = all_exceeded
