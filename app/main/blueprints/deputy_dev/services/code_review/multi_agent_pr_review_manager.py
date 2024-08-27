from torpedo import CONFIG

from app.main.blueprints.deputy_dev.constants.constants import (
    AgentTypes,
    MultiAgentReflectionIteration,
)
from app.main.blueprints.deputy_dev.services.code_review.agent_services.agent_factory import (
    AgentFactory,
)
from app.main.blueprints.deputy_dev.services.comment.comment_blending_engine import (
    CommentBlendingEngine,
)
from app.main.blueprints.deputy_dev.services.llm.multi_agents_manager import (
    MultiAgentsLLMManager,
)
from app.main.blueprints.deputy_dev.services.repo.base_repo import BaseRepo
from app.main.blueprints.deputy_dev.services.tiktoken import TikToken


class MultiAgentPRReviewManager:
    def __init__(self, repo_service: BaseRepo, prompt_version=None):
        self.repo_service = repo_service
        self.settings = CONFIG.config["PR_REVIEW_SETTINGS"]
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
        self.exclude_agent = []
        self.agent_factory = AgentFactory(
            repo_service=self.repo_service, reflection_enabled=self._is_reflection_enabled()
        )

    # section setting start

    def _is_reflection_enabled(self):
        if self.reflection_enabled is None:
            self.reflection_enabled = self.settings["REFLECTION_ENABLED"]
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
        self.exclude_agent.append(AgentTypes.PR_SUMMARY.value)  # Exclude summary in reflection call
        self.multi_agent_reflection_stage = MultiAgentReflectionIteration.PASS_2.value
        await self._build_prompts()

    # section prompt end

    # llm handler start
    async def _make_llm_calls(self):
        contexts = [self.current_prompts[key] for key in self.current_prompts]
        self.llm_comments = await MultiAgentsLLMManager.get_llm_response(contexts)
        return self.llm_comments

    # llm handler end

    # blending engine section start
    def filter_comments(self):
        self.filtered_comments = CommentBlendingEngine(self.llm_comments).blend_comments()

    # blending engine section end

    def populate_pr_summary(self):
        self.pr_summary = self.llm_comments.get(AgentTypes.PR_SUMMARY.value) or ""

    async def __execute_pass(self):
        await self._build_prompts()
        await self._make_llm_calls()
        self.populate_meta_info()

    async def execute_pass_1(self):
        await self.__execute_pass()
        self.populate_pr_summary()

    async def execute_pass_2(self):
        self.exclude_agent.append(AgentTypes.PR_SUMMARY.value)  # Exclude summary in reflection call
        self.multi_agent_reflection_stage = MultiAgentReflectionIteration.PASS_2.value
        await self.__execute_pass()

    async def get_code_review_comments(self):
        await self.execute_pass_1()
        await self.execute_pass_2() if self._is_reflection_enabled() else None
        self.filter_comments()
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
        return self.filtered_comments, self.pr_summary, self.agents_tokens, self.meta_info_to_save
