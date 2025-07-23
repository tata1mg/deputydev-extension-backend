from app.main.blueprints.deputy_dev.models.dao.postgres.ide_reviews_comments import IdeReviewsComments
from app.main.blueprints.deputy_dev.models.dao.postgres.user_agent_comment_mapping import UserAgentCommentMapping
from app.main.blueprints.deputy_dev.models.dto.user_agent_dto import UserAgentDTO
from app.main.blueprints.deputy_dev.models.dto.ide_reviews_comment_dto import IdeReviewsCommentDTO
from tortoise.query_utils import Prefetch
from typing import List, Union
from app.backend_common.repository.db import DB
from deputydev_core.utils.app_logger import AppLogger


class ExtensionCommentRepository:
    @classmethod
    async def get_review_comments(cls, review_id) -> list[IdeReviewsCommentDTO]:
        comments = (
            await IdeReviewsComments.filter(is_deleted=False, review_id=review_id, is_valid=True)
            .prefetch_related(
                Prefetch(
                    "user_agent_comment_mapping",
                    queryset=UserAgentCommentMapping.all().prefetch_related("agent"),
                )
            )
            .all()
        )
        comment_dtos = []
        for comment in comments:
            agents = []
            for user_agent_comment_mapping in comment.user_agent_comment_mapping:
                agents.append(UserAgentDTO(**dict(user_agent_comment_mapping.agent)))
            comment_dtos.append(IdeReviewsCommentDTO(**dict(comment), agents=agents))
        return comment_dtos

    @classmethod
    async def update_comments(cls, comment_ids, data):
        if comment_ids and data:
            await IdeReviewsComments.filter(id__in=comment_ids).update(**data)
    
    @classmethod
    async def update_comment(cls, comment_id, data):
        if comment_id and data:
            print("comment_id", comment_id)
            print("data", data)
            await IdeReviewsComments.filter(id=comment_id).update(**data)

    @classmethod
    async def insert_comments(cls, comments: list[IdeReviewsCommentDTO]):
        agent_comment_mappings = []
        for comment in comments:
            comment_to_insert = IdeReviewsComments(
                title=comment.title,
                review_id=comment.review_id,
                comment=comment.comment,
                rationale=comment.rationale,
                corrective_code=comment.corrective_code,
                is_deleted=comment.is_deleted,
                file_path=comment.file_path,
                line_hash=comment.line_hash,
                line_number=int(comment.line_number),
                tag=comment.tag,
                confidence_score=comment.confidence_score,
            )
            await comment_to_insert.save()
            for agent in comment.agents:
                agent_comment_mappings.append(
                    UserAgentCommentMapping(agent_id=agent.id, comment_id=comment_to_insert.id)
                )
        await UserAgentCommentMapping.bulk_create(agent_comment_mappings)

    @classmethod
    async def db_get(
            cls, filters, fetch_one=False, order_by=None
    ) -> Union[IdeReviewsCommentDTO, List[IdeReviewsCommentDTO]]:
        try:
            review_data = await DB.by_filters(
                model_name=IdeReviewsComments, where_clause=filters, fetch_one=fetch_one, order_by=order_by
            )
            if review_data and fetch_one:
                return IdeReviewsCommentDTO(**review_data)
            elif review_data:
                return [IdeReviewsCommentDTO(**review) for review in review_data]
        except Exception as ex:
            AppLogger.log_error(f"Error fetching extension review: {filters}, ex: {ex}")
            raise ex
