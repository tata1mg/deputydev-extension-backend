from sanic.log import logger

from app.backend_common.repository.db import DB
from app.main.blueprints.deputy_dev.models.dao.postgres.feedbacks import Feedbacks
from app.main.blueprints.deputy_dev.models.dto.feedback_dto import FeedbackDTO


class FeedbackService:
    @classmethod
    async def db_insert(cls, feedback_dto: FeedbackDTO) -> FeedbackDTO:
        try:
            payload = feedback_dto.dict()
            del payload["id"]
            row = await DB.insert_row(Feedbacks, payload)
            return row
        except Exception as ex:
            logger.error("not able to insert feedback details to db {} exception {}".format(feedback_dto.dict(), ex))
            raise ex
