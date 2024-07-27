from sanic.log import logger

from app.main.blueprints.deputy_dev.models.dao import PRComments
from app.main.blueprints.deputy_dev.models.dto.pr_comments_dto import PRCommentsDTO
from app.main.blueprints.deputy_dev.services.db.db import DB


class CommentService:
    @classmethod
    async def db_insert(cls, comment_dto: PRCommentsDTO):
        try:
            payload = comment_dto.dict()
            del payload["id"]
            row = await DB.insert_row(PRComments, payload)
            return row
        except Exception as ex:
            logger.error(
                "not able to insert pr details {} meta info {} exception {}".format(comment_dto.dict(), {}, ex)
            )
            raise ex

    @classmethod
    async def bulk_insert(cls, comment_daos: list[PRComments]):
        try:
            rows_inserted = await DB.bulk_create(PRComments, comment_daos)
            return rows_inserted
        except Exception as ex:
            logger.error("not able to insert pr details exception {}".format(ex))
            raise ex
