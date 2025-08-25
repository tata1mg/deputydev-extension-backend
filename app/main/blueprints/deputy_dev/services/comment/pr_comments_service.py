from sanic.log import logger

from app.backend_common.repository.db import DB
from app.main.blueprints.deputy_dev.models.dao.postgres import PRComments
from app.main.blueprints.deputy_dev.models.dto.pr_comments_dto import PRCommentsDTO


class CommentService:
    @classmethod
    async def db_insert(cls, comment_dto: PRCommentsDTO) -> PRComments:
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
    async def bulk_insert(cls, comment_daos: list[PRComments]) -> int:
        try:
            rows_inserted = await DB.bulk_create(PRComments, comment_daos)
            return rows_inserted
        except Exception as ex:
            logger.error("not able to insert pr details exception {}".format(ex))
            raise ex
