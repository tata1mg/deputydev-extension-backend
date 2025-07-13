from typing import List, Dict, Any, Optional
from app.main.blueprints.deputy_dev.services.repository.extension_reviews.repository import ExtensionReviewsRepository
from app.backend_common.repository.db import DB
from app.main.blueprints.deputy_dev.models.ide_review_history_params import ReviewHistoryParams


class ExtensionCodeReviewHistoryManager:
    async def fetch_reviews_by_filters(self, review_history_params: ReviewHistoryParams) -> List[Dict[str, Any]]:
        """
        Fetch extension reviews based on provided filters using DB class
        """
        user_team_id = review_history_params.user_team_id
        source_branch = review_history_params.source_branch
        target_branch = review_history_params.target_branch
        repo_id = review_history_params.repo_id
        try:
            # Build where clause for reviews
            where_clause = {}

            # Add filters based on provided parameters
            if repo_id:
                where_clause["repo_id"] = repo_id
            if source_branch:
                where_clause["source_branch"] = source_branch
            if target_branch:
                where_clause["target_branch"] = target_branch
            if user_team_id:
                where_clause["user_team_id"] = user_team_id
            where_clause["review_status__not"] = "cancelled"
            reviews = await ExtensionReviewsRepository.fetch_reviews_history(filters=where_clause)
            result = [review.model_dump(mode="json") for review in reviews]
            return result

        except Exception as e:
            # Log the error and return empty list
            print(f"Error fetching reviews: {str(e)}")
            return []

    async def get_review_count_by_filters(
        self,
        user_team_id: Optional[int] = None,
        source_branch: Optional[str] = None,
        target_branch: Optional[str] = None,
        repo_id: Optional[int] = None,
    ) -> int:
        """
        Get count of reviews matching the filters using DB class
        """
        try:
            where_clause = {}

            if repo_id:
                where_clause["repo_id"] = repo_id
            if source_branch:
                where_clause["source_branch"] = source_branch
            if target_branch:
                where_clause["target_branch"] = target_branch

            if user_team_id:
                repo_filters = {"team_id": user_team_id}
                matching_repos = await DB.by_filters(
                    model_name="dao.Repos", where_clause=repo_filters, fetch_one=False, only=["id"]
                )
                repo_ids = [repo["id"] for repo in matching_repos]

                if repo_ids:
                    where_clause["repo_id__in"] = repo_ids
                else:
                    return 0

            count = await DB.count_by_filters(model_name="dao.ExtensionReviews", filters=where_clause)

            return count

        except Exception as e:
            print(f"Error counting reviews: {str(e)}")
            return 0
