from typing import Any, Dict, List, Optional

from deputydev_core.services.chunking.chunk_info import ChunkInfo
from deputydev_core.services.chunking.utils.snippet_renderer import render_snippet_array

from app.common.utils.context_vars import get_context_value
from app.main.blueprints.deputy_dev.services.code_review.agents.base_code_review_agent import (
    BaseCodeReviewAgent,
)
from app.main.blueprints.deputy_dev.services.code_review.context.context_service import (
    ContextService,
)
from app.main.blueprints.deputy_dev.services.code_review.prompts.dataclasses.main import (
    PromptFeatures,
)
from app.main.blueprints.deputy_dev.utils import repo_meta_info_prompt

from ...dataclasses.main import AgentTypes


class BaseCommenterAgent(BaseCodeReviewAgent):
    is_dual_pass: bool
    prompt_features: List[PromptFeatures]

    def __init__(self, context_service: ContextService, is_reflection_enabled: bool, agent_setting: Dict[str, Any]):
        self.agent_setting = agent_setting
        self.agent_id = self.agent_setting.get("agent_id")
        super().__init__(context_service, is_reflection_enabled)

    def agent_relevant_chunk(self, relevant_chunks: Dict[str, Any]) -> str:
        relevant_chunks_index = relevant_chunks["relevant_chunks_mapping"][self.agent_id]
        agent_relevant_chunks: List[ChunkInfo] = []
        for index in relevant_chunks_index:
            agent_relevant_chunks.append(relevant_chunks["relevant_chunks"][index])
        return render_snippet_array(agent_relevant_chunks)

    async def required_prompt_variables(self, comments: Optional[str] = None) -> Dict[str, Optional[str]]:
        relevant_chunks = await self.context_service.agent_wise_relevant_chunks()
        return {
            "PULL_REQUEST_TITLE": self.context_service.get_pr_title(),
            "PULL_REQUEST_DESCRIPTION": self.context_service.get_pr_description(),
            "PULL_REQUEST_DIFF": await self.context_service.get_pr_diff(
                append_line_no_info=True, agent_id=self.agent_id
            ),
            "REVIEW_COMMENTS_BY_JUNIOR_DEVELOPER": comments,
            "CONTEXTUALLY_RELATED_CODE_SNIPPETS": self.agent_relevant_chunk(relevant_chunks),
            "USER_STORY": await self.context_service.get_user_story(),
            "PRODUCT_RESEARCH_DOCUMENT": await self.context_service.get_confluence_doc(),
            "PR_DIFF_WITHOUT_LINE_NUMBER": await self.context_service.get_pr_diff(agent_id=self.agent_id),
            "AGENT_OBJECTIVE": self.agent_setting.get("objective", ""),
            "CUSTOM_PROMPT": self.agent_setting.get("custom_prompt") or "",
            "BUCKET": self.agent_setting.get("display_name"),
            "REPO_INFO_PROMPT": repo_meta_info_prompt(get_context_value("setting").get("app", {})),
            "AGENT_NAME": self.agent_type.value,
        }

    def get_additional_info_prompt(self, tokens_info, reflection_iteration):
        return {
            "key": self.agent_name,
            "comment_confidence_score": self.agent_setting.get("confidence_score"),
            "model": self.model,
            "tokens": tokens_info,
            "reflection_iteration": reflection_iteration,
        }
