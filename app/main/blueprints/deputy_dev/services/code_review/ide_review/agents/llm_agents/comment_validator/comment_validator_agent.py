import json
from typing import Any, Dict, List, Optional

from app.main.blueprints.deputy_dev.services.code_review.common.agents.dataclasses.main import (
    AgentTypes,
)
from app.main.blueprints.deputy_dev.services.code_review.common.comments.dataclasses.main import (
    ParsedCommentData,
)
from app.main.blueprints.deputy_dev.services.code_review.common.prompts.dataclasses.main import (
    PromptFeatures,
)
from app.main.blueprints.deputy_dev.services.code_review.ide_review.agents.base_code_review_agent import (
    BaseCodeReviewAgent,
)
from app.main.blueprints.deputy_dev.services.code_review.ide_review.context.ide_review_context_service import (
    IdeReviewContextService,
)
from deputydev_core.llm_handler.core.handler import LLMHandler
from deputydev_core.llm_handler.models.dto.message_thread_dto import LLModels


class CommentValidatorAgent(BaseCodeReviewAgent):
    is_dual_pass = False
    prompt_features = [
        PromptFeatures.COMMENT_VALIDATION,
    ]
    agent_type = AgentTypes.COMMENT_VALIDATION

    def __init__(
        self,
        context_service: IdeReviewContextService,
        comments: List[ParsedCommentData],
        llm_handler: LLMHandler[PromptFeatures],
        model: LLModels,
    ) -> None:
        self.comments = comments
        super().__init__(context_service, llm_handler, model)

    async def required_prompt_variables(self, last_pass_result: Optional[Any] = None) -> Dict[str, Optional[str]]:
        return {
            "COMMENTS": json.dumps([comment.model_dump(mode="json") for comment in self.comments]),
            "PR_DIFF": await self.context_service.get_pr_diff(append_line_no_info=True),
        }
