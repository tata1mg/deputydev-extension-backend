from app.main.blueprints.deputy_dev.models.dao.postgres.extension_reviews import ExtensionReviews
from app.main.blueprints.deputy_dev.models.dao.postgres.ide_reviews_comments import IdeReviewsComments


class ExtensionCommentRepository:
    async def get_review_comments(self, review_id):
        comments = await IdeReviewsComments.filter(review_id=review_id, status="valid")
        return comments

