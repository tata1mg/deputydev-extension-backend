import json
from typing import Any, Dict, List, Optional

from deputydev_core.llm_handler.core.handler import LLMHandler
from deputydev_core.llm_handler.models.dto.message_thread_dto import LLModels
from deputydev_core.services.chunking.utils.snippet_renderer import render_snippet_array

from app.main.blueprints.deputy_dev.services.code_review.common.agents.dataclasses.main import (
    AgentTypes,
)
from app.main.blueprints.deputy_dev.services.code_review.common.comments.dataclasses.main import (
    ParsedCommentData,
)
from app.main.blueprints.deputy_dev.services.code_review.common.prompts.dataclasses.main import (
    PromptFeatures,
)
from app.main.blueprints.deputy_dev.services.code_review.vcs_review.agents.base_code_review_agent import (
    BaseCodeReviewAgent,
)
from app.main.blueprints.deputy_dev.services.code_review.vcs_review.context.context_service import (
    ContextService,
)


class CommentValidatorAgent(BaseCodeReviewAgent):
    is_dual_pass = False
    prompt_features = [
        PromptFeatures.COMMENT_VALIDATION,
    ]
    agent_type = AgentTypes.COMMENT_VALIDATION

    def __init__(
        self,
        context_service: ContextService,
        comments: List[ParsedCommentData],
        is_reflection_enabled: bool,
        agent_setting: Dict[str, Any],
        llm_handler: LLMHandler[PromptFeatures],
        model: LLModels,
    ) -> None:
        self.comments = comments
        self.agent_setting = agent_setting
        self.agent_id = self.agent_setting.get("agent_id")
        super().__init__(context_service, is_reflection_enabled, llm_handler, model)

    def agent_relevant_chunk(self, relevant_chunks: Dict[str, Any]) -> str:
        relevant_chunks_indexes = relevant_chunks["comment_validation_relevant_chunks_mapping"]
        chunks = [relevant_chunks["relevant_chunks"][index] for index in relevant_chunks_indexes]
        return render_snippet_array(chunks)

    async def required_prompt_variables(self, last_pass_result: Optional[Any] = None) -> Dict[str, Optional[str]]:
        return {
            "COMMENTS": json.dumps([comment.model_dump(mode="json") for comment in self.comments]),
            "PR_DIFF": await self.context_service.get_pr_diff(append_line_no_info=True),
        }
