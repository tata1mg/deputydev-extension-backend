from typing import Optional

from sanic.log import logger

from app.backend_common.repository.db import DB
from app.main.blueprints.one_dev.models.dao.postgres.ide_feedbacks import (
    IdeFeedbacks,
)
from app.main.blueprints.one_dev.models.dto.extension_feedbacks_dto import (
    ExtensionFeedbacksDTO,
)


class ExtensionFeedbacksRepository:
    @classmethod
    async def get_feedback_by_query_id(cls, query_id: int) -> Optional[ExtensionFeedbacksDTO]:
        try:
            extension_feedback = await DB.by_filters(
                model_name=IdeFeedbacks,
                where_clause={"query_id": query_id},
                fetch_one=True,
            )
            if not extension_feedback:
                return None
            return ExtensionFeedbacksDTO(**extension_feedback)
        except Exception as ex:
            logger.error(f"error occurred while getting extension_feedback in db for query_id : {query_id}, ex: {ex}")
            raise ex

    @classmethod
    async def submit_feedback(cls, query_id: int, feedback: str) -> None:
        try:
            if await cls.get_feedback_by_query_id(query_id):
                await DB.update_with_filters(
                    None,
                    model=IdeFeedbacks,
                    payload={"feedback": feedback},
                    where_clause={"query_id": query_id},
                    update_fields=["feedback", "updated_at"],
                )
            else:
                await DB.create(model=IdeFeedbacks, payload={"query_id": query_id, "feedback": feedback})
        except Exception as ex:
            logger.error(
                f"error occurred while creating/updating extension_feedback in db for query_id : {query_id}, ex: {ex}"
            )
            raise ex
