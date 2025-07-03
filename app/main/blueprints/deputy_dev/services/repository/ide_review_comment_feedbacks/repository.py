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
            return IdeReviewCommentFeedbackDTO(**row)
        except Exception as ex:
            logger.error(f"Error inserting ide_review_comment_feedback: {feedback_dto.dict()}, ex: {ex}")
            raise ex
