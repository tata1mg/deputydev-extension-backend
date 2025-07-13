from app.main.blueprints.deputy_dev.models.dao.postgres.user_agent_comment_mapping import UserAgentCommentMapping
from app.main.blueprints.deputy_dev.models.dao.postgres.ide_reviews_comments import IdeReviewsComments
from app.main.blueprints.deputy_dev.models.dto.user_agent_dto import UserAgentDTO
from app.main.blueprints.deputy_dev.models.dto.ide_reviews_comment_dto import IdeReviewsCommentDTO
from tortoise.query_utils import Prefetch


class ExtensionCommentRepository:
    async def get_review_comments(self, review_id) -> list[IdeReviewsCommentDTO]:
        comments = await IdeReviewsComments.filter(
            is_deleted=False, review_id=review_id, is_valid=True
        ).prefetch_related(
            Prefetch(
                "user_agent_comment_mapping",
                queryset=UserAgentCommentMapping.all().prefetch_related("agent"),
            )
        ).all()
        comment_dtos = []
        for comment in comments:
            agents = []
            for user_agent_comment_mapping in comment.user_agent_comment_mappings:
                agents.append(UserAgentDTO(**dict(user_agent_comment_mapping.agent)))
            comment_dtos.append(IdeReviewsCommentDTO(**dict(comment), agents=agents))
        return comment_dtos
