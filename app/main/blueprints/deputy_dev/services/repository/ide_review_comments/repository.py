from typing import Any, Dict, List, Union

from git import Optional
from sanic.log import logger

from app.backend_common.repository.db import DB
from app.main.blueprints.deputy_dev.models.dao.postgres.ide_reviews_comments import IdeReviewsComments
from app.main.blueprints.deputy_dev.models.dto.ide_reviews_comment_dto import IdeReviewsCommentDTO


class IdeReviewsCommentsRepository:
    @classmethod
    async def db_get(
        cls, filters: Dict[str, Any], fetch_one: bool = False
    ) -> Optional[Union[IdeReviewsCommentDTO, List[IdeReviewsCommentDTO]]]:
        try:
            data = await DB.by_filters(model_name=IdeReviewsComments, where_clause=filters, fetch_one=fetch_one)
            if data and fetch_one:
                return IdeReviewsCommentDTO(**data)
            elif data:
                return [IdeReviewsCommentDTO(**item) for item in data]
        except Exception as ex:
            logger.error(f"Error fetching ide_reviews_comments: {filters}, ex: {ex}")
            raise ex

    @classmethod
    async def db_insert(cls, comment_dto: IdeReviewsCommentDTO) -> IdeReviewsCommentDTO:
        try:
            payload = comment_dto.dict()
            del payload["id"]
            row = await DB.insert_row(IdeReviewsComments, payload)
            return IdeReviewsCommentDTO(**row)
        except Exception as ex:
            logger.error(f"Error inserting ide_reviews_comment: {comment_dto.dict()}, ex: {ex}")
            raise ex
