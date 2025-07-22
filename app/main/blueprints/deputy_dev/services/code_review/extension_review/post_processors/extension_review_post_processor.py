from app.main.blueprints.deputy_dev.services.code_review.common.prompts.dataclasses.main import (
    PromptFeatures,
)
from app.main.blueprints.deputy_dev.services.code_review.extension_review.prompts.factory import (
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
from app.main.blueprints.deputy_dev.services.code_review.extension_review.comments.comment_blending_engine import (
    CommentBlendingEngine,
)
from app.main.blueprints.deputy_dev.services.code_review.extension_review.comments.dataclasses.main import (
    LLMCommentData,
)
from app.main.blueprints.deputy_dev.models.dto.ide_reviews_comment_dto import IdeReviewsCommentDTO
from app.main.blueprints.deputy_dev.models.dto.user_agent_dto import UserAgentDTO


class ExtensionReviewPostProcessor:
    @classmethod
    async def post_process_pr(cls, data, user_team_id: int):
        review_id = data.get("review_id")
        review = await ExtensionReviewsRepository.db_get(filters={"id": review_id}, fetch_one=True)
        comments = await ExtensionCommentRepository.get_review_comments(review_id)
        formatted_comments = cls.format_comments(comments)
        context_service = ExtensionContextService(review_id=review_id)
        user_agents = await UserAgentRepository.db_get({"user_team_id": user_team_id})
        llm_handler = LLMHandler(
            prompt_factory=PromptFeatureFactory,
            prompt_features=PromptFeatures,
            cache_config=PromptCacheConfig(conversation=True, tools=True, system_message=True),
        )
        comment_blending_service = CommentBlendingEngine(
            llm_comments=formatted_comments,
            session_id=review.session_id,
            context_service=context_service,
            agents=user_agents,
            llm_handler=llm_handler,
        )
        filtered_comments, agent_results, review_title = await comment_blending_service.blend_comments()
        valid_comment_ids = set([comment.id for comment in filtered_comments if comment.id and comment.is_valid])
        invalid_comment_ids = [comment.id for comment in comments if comment.id not in valid_comment_ids]
        await ExtensionCommentRepository.update_comments(invalid_comment_ids, {"is_valid": False})
        comments_to_insert = []
        for comment in filtered_comments:
            # blended comment
            if not comment.id:
                blended_comment = IdeReviewsCommentDTO(
                    review_id=review_id,
                    title=comment.title,
                    comment=comment.comment,
                    confidence_score=comment.confidence_score,
                    rationale=comment.rationale,
                    corrective_code=comment.corrective_code,
                    file_path=comment.file_path,
                    line_hash=comment.line_hash,
                    line_number=comment.line_number,
                    tag=comment.tag,
                    is_valid=True,
                    agents=[UserAgentDTO(id=agent.agent_id) for agent in comment.buckets],
                )
                comments_to_insert.append(blended_comment)
        await ExtensionCommentRepository.insert_comments(comments_to_insert)
        review_data = {"review_status": "Completed", "title": review_title}
        await ExtensionReviewsRepository.update_review(review_id, review_data)
        return {"status": "Completed"}

    @classmethod
    def format_comments(cls, comments: list[IdeReviewsCommentDTO]):
        comments_by_agent_name = {}
        for comment in comments:
            for agent in comment.agents:
                if agent.agent_name not in comments_by_agent_name:
                    comments_by_agent_name[agent.agent_name] = []
                formatted_comment = LLMCommentData(
                    id=comment.id,
                    title=comment.title,
                    comment=comment.comment,
                    corrective_code=comment.corrective_code,
                    file_path=comment.file_path,
                    line_number=comment.line_number,
                    line_hash=comment.line_hash,
                    tag=comment.tag,
                    confidence_score=comment.confidence_score,
                    rationale=comment.rationale,
                    bucket=agent.display_name,
                )
                comments_by_agent_name[agent.agent_name].append(formatted_comment)
        return comments_by_agent_name
