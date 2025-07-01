from app.main.blueprints.deputy_dev.services.code_review.base_pr_review_manager import (
    BasePRReviewManager,
)


class ExtensionCodeReviewHistoryManager(BasePRReviewManager):

    def fetch_all_reviews(self):
