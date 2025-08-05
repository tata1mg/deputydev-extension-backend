from typing import List, Union

from sanic.log import logger

from app.backend_common.repository.db import DB
from app.main.blueprints.deputy_dev.models.dao.postgres.ide_review_feedback import IdeReviewFeedback
from app.main.blueprints.deputy_dev.models.dto.ide_review_feedback_dto import IdeReviewFeedbackDTO


class IdeReviewFeedbacksRepository:
    @classmethod
    async def db_get(cls, filters, fetch_one=False) -> Union[IdeReviewFeedbackDTO, List[IdeReviewFeedbackDTO]]:
        try:
            data = await DB.by_filters(model_name=IdeReviewFeedback, where_clause=filters, fetch_one=fetch_one)
            if data and fetch_one:
                return IdeReviewFeedbackDTO(**data)
            elif data:
                return [IdeReviewFeedbackDTO(**item) for item in data]
        except Exception as ex:
            logger.error(f"Error fetching ide_review_comment_feedbacks: {filters}, ex: {ex}")
            raise ex

    @classmethod
    async def db_insert(cls, feedback_dto: IdeReviewFeedbackDTO) -> IdeReviewFeedbackDTO:
        try:
            payload = feedback_dto.dict()
            del payload["id"]
            row = await DB.insert_row(IdeReviewFeedback, payload)
            return IdeReviewFeedbackDTO(**dict(row))
        except Exception as ex:
            logger.error(f"Error inserting extension_review_feedback: {feedback_dto.dict()}, ex: {ex}")
            raise ex
