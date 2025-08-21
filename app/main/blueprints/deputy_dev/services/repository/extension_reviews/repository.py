from collections import defaultdict
from typing import Any, Dict, List, Optional, Union

from sanic.log import logger
from tortoise.query_utils import Prefetch

from app.backend_common.repository.db import DB
from app.main.blueprints.deputy_dev.models.dao.postgres.ide_review_comment_feedbacks import IdeReviewCommentFeedbacks
from app.main.blueprints.deputy_dev.models.dao.postgres.ide_review_feedback import IdeReviewFeedback
from app.main.blueprints.deputy_dev.models.dao.postgres.ide_reviews import IdeReviews
from app.main.blueprints.deputy_dev.models.dao.postgres.ide_reviews_comments import IdeReviewsComments
from app.main.blueprints.deputy_dev.models.dao.postgres.user_agent_comment_mapping import UserAgentCommentMapping
from app.main.blueprints.deputy_dev.models.dto.ide_review_comment_feedback_dto import IdeReviewCommentFeedbackDTO
from app.main.blueprints.deputy_dev.models.dto.ide_review_dto import IdeReviewDTO
from app.main.blueprints.deputy_dev.models.dto.ide_review_feedback_dto import IdeReviewFeedbackDTO
from app.main.blueprints.deputy_dev.models.dto.ide_reviews_comment_dto import IdeReviewsCommentDTO
from app.main.blueprints.deputy_dev.models.dto.user_agent_dto import UserAgentDTO


class ExtensionReviewsRepository:
    @classmethod
    async def db_get(
        cls, filters: Dict[str, Any], fetch_one: bool = False, order_by: Optional[str] = None
    ) -> Union[IdeReviewDTO, List[IdeReviewDTO]]:
        try:
            review_data = await DB.by_filters(
                model_name=IdeReviews, where_clause=filters, fetch_one=fetch_one, order_by=order_by
            )
            if review_data and fetch_one:
                return IdeReviewDTO(**review_data)
            elif review_data:
                return [IdeReviewDTO(**review) for review in review_data]
        except Exception as ex:
            logger.error(f"Error fetching Ide review: {filters}, ex: {ex}")
            raise ex

    @classmethod
    async def db_insert(cls, review_dto: IdeReviewDTO) -> IdeReviewDTO:
        try:
            payload = review_dto.dict()
            del payload["id"]
            row = await DB.insert_row(IdeReviews, payload)
            row_dict = await row.to_dict()
            return IdeReviewDTO(**row_dict)
        except Exception as ex:
            logger.error(f"Error inserting Ide review: {review_dto.dict()}, ex: {ex}")
            raise ex

    @classmethod
    async def fetch_reviews_history(cls, filters: dict, order_by: str = "-created_at") -> list[IdeReviewDTO]:
        try:
            reviews = await cls._fetch_reviews_with_comments(filters, order_by)
            comment_ids = cls._extract_comment_ids(reviews)
            comment_feedback_map = await cls._fetch_comment_feedback_map(comment_ids)
            comment_agents_map = await cls._fetch_comment_agents_map(comment_ids)
            review_dtos = cls._build_review_dtos(reviews, comment_agents_map, comment_feedback_map)
            return review_dtos
        except Exception as ex:
            logger.error(f"Error fetching review history: {filters}, ex: {ex}")
            raise ex

    @classmethod
    async def _fetch_reviews_with_comments(cls, filters: dict, order_by: str) -> list[IdeReviews]:
        filtered_comments = IdeReviewsComments.filter(is_deleted=False, is_valid=True)
        filtered_feedbacks = IdeReviewFeedback.all()
        return (
            await IdeReviews.filter(**filters)
            .order_by(order_by)
            .prefetch_related(
                Prefetch("review_comments", queryset=filtered_comments),
                Prefetch("review_feedback", queryset=filtered_feedbacks),
            )
        )

    @classmethod
    async def _fetch_comment_feedback_map(cls, comment_ids: List[int]) -> dict[int, IdeReviewCommentFeedbackDTO]:
        try:
            feedbacks = await IdeReviewCommentFeedbacks.filter(comment_id__in=comment_ids)
            comment_feedback_map = defaultdict(IdeReviewCommentFeedbackDTO)
            for feedback in feedbacks:
                comment_feedback_map[feedback.comment_id] = IdeReviewCommentFeedbackDTO(**dict(feedback))
            return comment_feedback_map
        except Exception as ex:
            logger.error(f"Error fetching comment feedback map: {comment_ids}, ex: {ex}")
            raise ex

    @classmethod
    def _extract_comment_ids(cls, reviews: list[IdeReviews]) -> list[int]:
        comment_ids = []
        for review in reviews:
            for comment in review.review_comments:
                comment_ids.append(comment.id)
        return comment_ids

    @classmethod
    async def _fetch_comment_agents_map(cls, comment_ids: list[int]) -> dict[int, list[UserAgentDTO]]:
        comment_agent_mappings = await UserAgentCommentMapping.filter(comment_id__in=comment_ids).prefetch_related(
            "agent"
        )
        comment_agents_map = defaultdict(list)
        for mapping in comment_agent_mappings:
            dto = UserAgentDTO(**dict(mapping.agent))
            comment_agents_map[mapping.comment_id].append(dto)
        return comment_agents_map

    @classmethod
    def _build_review_dtos(
        cls,
        reviews: list[IdeReviews],
        comment_agents_map: dict[int, list[UserAgentDTO]],
        comment_feedback_map: dict[int, list[IdeReviewCommentFeedbackDTO]],
    ) -> list[IdeReviewDTO]:
        review_dtos = []
        for review in reviews:
            comments_dto = []
            for comment in review.review_comments:
                if not comment.is_deleted:
                    agents = comment_agents_map.get(comment.id, [])
                    feedback = comment_feedback_map.get(comment.id)
                    comment_dto = IdeReviewsCommentDTO(**dict(comment), agents=agents, feedback=feedback)
                    comments_dto.append(comment_dto)

            review_dto = IdeReviewDTO(**dict(review))
            review_dto.comments = comments_dto
            review_dto.feedback = (
                IdeReviewFeedbackDTO(**dict(review.review_feedback[0])) if review.review_feedback else None
            )
            review_dtos.append(review_dto)
        return review_dtos

    @classmethod
    async def update_review(cls, review_id: int, data: dict) -> None:
        if data and review_id:
            await IdeReviews.filter(id=review_id).update(**data)
