from app.main.blueprints.deputy_dev.services.code_review.common.prompts.dataclasses.main import (
    PromptFeatures,
)
from app.main.blueprints.deputy_dev.services.code_review.common.prompts.factory import (
    PromptFeatureFactory,
)

from app.backend_common.services.llm.dataclasses.main import PromptCacheConfig
from app.backend_common.services.llm.handler import LLMHandler
from app.main.blueprints.deputy_dev.services.repository.extension_comments.repository import ExtensionCommentRepository
from app.main.blueprints.deputy_dev.services.repository.extension_reviews.repository import ExtensionReviewsRepository
from app.main.blueprints.deputy_dev.services.repository.user_agents.repository import UserAgentRepository
from app.main.blueprints.deputy_dev.services.code_review.extension_review.context.extension_context_service import (
    ExtensionContextService,
)
from app.main.blueprints.deputy_dev.models.dto.ide_reviews_comment_dto import IdeReviewsCommentDTO
from app.main.blueprints.deputy_dev.services.code_review.extension_review.comments.comment_blending_engine import CommentBlendingEngine
from app.main.blueprints.deputy_dev.services.code_review.extension_review.comments.dataclasses.main import AgentRunResult, Comment


class ExtensionReviewPostProcessor:
    async def post_process_pr(self, data, user_team_id: int):
        review_id = data.get("review_id")
        review = await ExtensionReviewsRepository.db_get(filters={"id": review_id}, fetch_one=True)
        comments = await ExtensionCommentRepository().get_review_comments(review_id)
        formatted_comments = self.format_comments(comments)
        context_service = ExtensionContextService(review_id=review_id)
        code_diff = await context_service.get_pr_diff()
        user_agents = UserAgentRepository.db_get({"user_team_id": user_team_id})
        llm_handler = LLMHandler(
            prompt_factory=PromptFeatureFactory,
            prompt_features=PromptFeatures,
            cache_config=PromptCacheConfig(conversation=True, tools=True, system_message=True),
        )
        comment_blending_service = CommentBlendingEngine(
            llm_comments=formatted_comments,
            session_id=review.session_id,
            context_service=context_service,
            agents=user_agents
        )



    def format_comments(self, comments: list[IdeReviewsCommentDTO]):
        comments_by_agent_name = {}
        for comment in comments:
            for agent in comment.agents:
                if agent.agent_name not in comments_by_agent_name:
                    comments_by_agent_name[agent.agent_name] = []
                formatted_comment = Comment(
                    comment=comment.comment,
                    corrective_code=comment.corrective_code,
                    file_path=comment.file_path,
                    line_number=comment.line_number,
                    confidence_score=comment.confidence_score,
                    rationale=comment.rationale,
                    bucket=agent.display_name,
                )
                comments_by_agent_name[agent.agent_name].append(formatted_comment)
        return comments_by_agent_name



