from typing import List, Union
from sanic.log import logger
from app.main.blueprints.deputy_dev.models.dao.postgres.extension_review_feedback import ExtensionReviewFeedback
from app.main.blueprints.deputy_dev.models.dto.extension_review_feedback_dto import ExtensionReviewFeedbackDTO
from app.backend_common.repository.db import DB


class ExtensionReviewFeedbacksRepository:
    @classmethod
    async def db_get(
        cls, filters, fetch_one=False
    ) -> Union[ExtensionReviewFeedbackDTO, List[ExtensionReviewFeedbackDTO]]:
        try:
            data = await DB.by_filters(model_name=ExtensionReviewFeedback, where_clause=filters, fetch_one=fetch_one)
            if data and fetch_one:
                return ExtensionReviewFeedbackDTO(**data)
            elif data:
                return [ExtensionReviewFeedbackDTO(**item) for item in data]
        except Exception as ex:
            logger.error(f"Error fetching ide_review_comment_feedbacks: {filters}, ex: {ex}")
            raise ex

    @classmethod
    async def db_insert(cls, feedback_dto: ExtensionReviewFeedbackDTO) -> ExtensionReviewFeedbackDTO:
        try:
            payload = feedback_dto.dict()
            del payload["id"]
            row = await DB.insert_row(ExtensionReviewFeedback, payload)
            return ExtensionReviewFeedbackDTO(**dict(row))
        except Exception as ex:
            logger.error(f"Error inserting extension_review_feedback: {feedback_dto.dict()}, ex: {ex}")
            raise ex
