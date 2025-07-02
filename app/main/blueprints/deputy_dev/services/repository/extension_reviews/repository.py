from typing import List, Union, Optional
from sanic.log import logger
from app.main.blueprints.deputy_dev.models.dao.postgres.extension_reviews import ExtensionReviews
from app.main.blueprints.deputy_dev.models.dto.extension_review_dto import ExtensionReviewDTO
from app.backend_common.repository.db import DB
from app.main.blueprints.deputy_dev.models.dto.ide_reviews_comment_dto import IdeReviewsCommentDTO

class ExtensionReviewsRepository:
    @classmethod
    async def db_get(cls, filters, fetch_one=False, order_by=None) -> Union[ExtensionReviewDTO, List[ExtensionReviewDTO]]:
        try:
            review_data = await DB.by_filters(model_name=ExtensionReviews, where_clause=filters, fetch_one=fetch_one, order_by=order_by)
            if review_data and fetch_one:
                return ExtensionReviewDTO(**review_data)
            elif review_data:
                return [ExtensionReviewDTO(**review) for review in review_data]
        except Exception as ex:
            logger.error(f"Error fetching extension review: {filters}, ex: {ex}")
            raise ex

    @classmethod
    async def db_insert(cls, review_dto: ExtensionReviewDTO) -> ExtensionReviewDTO:
        try:
            payload = review_dto.dict()
            del payload["id"]
            row = await DB.insert_row(ExtensionReviews, payload)
            return ExtensionReviewDTO(**row)
        except Exception as ex:
            logger.error(f"Error inserting extension review: {review_dto.dict()}, ex: {ex}")
            raise ex

    @classmethod
    async def find_or_create(cls, user_repo_id: int, reviewed_files: dict, loc: int, status: str, **kwargs) -> ExtensionReviewDTO:
        # You may want to define what makes a review unique (e.g., user_repo_id + reviewed_files hash)
        filters = {
            "user_repo_id": user_repo_id,
            "reviewed_files": reviewed_files,
            "is_deleted": False
        }
        review_dto = await cls.db_get(filters=filters, fetch_one=True)
        if not review_dto:
            review_data = {
                "user_repo_id": user_repo_id,
                "reviewed_files": reviewed_files,
                "loc": loc,
                "status": status,
                **kwargs
            }
            review_dto = await cls.db_insert(ExtensionReviewDTO(**review_data))
        return review_dto


    @classmethod
    async def fetch_reviews_history(cls, filters, order_by="-created_at"):
        try:
            reviews = await ExtensionReviews.filter(**filters).order_by(order_by).prefetch_related("review_comments")
            review_dtos = []
            for review in reviews:
                comments = []
                for comment in review.review_comments:
                    if not comment.is_deleted:
                        comments.append(IdeReviewsCommentDTO(**dict(comment)))
                review_dto = ExtensionReviewDTO(**dict(review))
                review_dto.comments = comments
                review_dtos.append(review_dto)
            return review_dtos
        except Exception as ex:
            logger.error(f"Error fetching review history: {filters}, ex: {ex}")
            raise ex

