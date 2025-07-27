from typing import List, Union
from sanic.log import logger
from app.main.blueprints.deputy_dev.models.dao.postgres.ide_review_comment_feedbacks import IdeReviewCommentFeedbacks
from app.main.blueprints.deputy_dev.models.dto.ide_review_comment_feedback_dto import IdeReviewCommentFeedbackDTO
from app.backend_common.repository.db import DB


class IdeReviewCommentFeedbacksRepository:
    @classmethod
    async def db_get(
        cls, filters, fetch_one=False
    ) -> Union[IdeReviewCommentFeedbackDTO, List[IdeReviewCommentFeedbackDTO]]:
        try:
            data = await DB.by_filters(model_name=IdeReviewCommentFeedbacks, where_clause=filters, fetch_one=fetch_one)
            if data and fetch_one:
                return IdeReviewCommentFeedbackDTO(**data)
            elif data:
                return [IdeReviewCommentFeedbackDTO(**item) for item in data]
        except Exception as ex:
            logger.error(f"Error fetching ide_review_comment_feedbacks: {filters}, ex: {ex}")
            raise ex

    @classmethod
    async def db_insert(cls, feedback_dto: IdeReviewCommentFeedbackDTO) -> IdeReviewCommentFeedbackDTO:
        try:
            payload = feedback_dto.dict()
            del payload["id"]
            row = await DB.insert_row(IdeReviewCommentFeedbacks, payload)
            return IdeReviewCommentFeedbackDTO(**dict(row))
        except Exception as ex:
            logger.error(f"Error inserting ide_review_comment_feedback: {feedback_dto.dict()}, ex: {ex}")
            raise ex

    @classmethod
    async def db_upsert(
        cls,
        feedback_dto: IdeReviewCommentFeedbackDTO
    ) -> IdeReviewCommentFeedbackDTO:
        """
        Update an existing feedback for a comment or insert a new one if it doesn't exist.
        The method checks for an existing feedback using the comment_id.

        Args:
            feedback_dto: The feedback DTO containing the data to upsert.
                        Must include a valid comment_id.

        Returns:
            IdeReviewCommentFeedbackDTO: The created or updated feedback as a DTO.

        Raises:
            Exception: If there's an error during the upsert operation.
        """
        try:
            payload = feedback_dto.model_dump()
            del payload["id"]
            existing = await cls.db_get(filters={"comment_id": feedback_dto.comment_id}, fetch_one=True)
            if existing:
                await DB.update_by_filters(
                    row=IdeReviewCommentFeedbacks,
                    model_name=IdeReviewCommentFeedbacks,
                    where_clause={"id": existing.id},
                    payload=payload
                )
                updated = await cls.db_get(filters={"id": existing.id}, fetch_one=True)
                return updated
            return await cls.db_insert(feedback_dto)

        except Exception as ex:
            logger.error(
                f"Error upserting ide_review_comment_feedback: {feedback_dto.model_dump()}, "
                f"ex: {ex}"
            )
            raise ex
