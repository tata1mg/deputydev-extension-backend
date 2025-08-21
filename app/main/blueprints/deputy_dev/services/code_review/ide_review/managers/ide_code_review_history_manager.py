from collections import defaultdict
from typing import Any, Dict, List, Optional

from deputydev_core.utils.app_logger import AppLogger

from app.backend_common.repository.db import DB
from app.main.blueprints.deputy_dev.models.dto.ide_review_dto import IdeReviewDTO
from app.main.blueprints.deputy_dev.models.ide_review_history_params import ReviewHistoryParams
from app.main.blueprints.deputy_dev.services.code_review.ide_review.dataclass.main import CommentUpdateRequest
from app.main.blueprints.deputy_dev.services.repository.extension_reviews.repository import ExtensionReviewsRepository
from app.main.blueprints.deputy_dev.services.repository.ide_reviews_comments.repository import IdeCommentRepository


class IdeCodeReviewHistoryManager:
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
            where_clause = {"review_status": "Completed", "is_deleted": False}
            # Add filters based on provided parameters
            if repo_id:
                where_clause["repo_id"] = repo_id
            if source_branch:
                where_clause["source_branch"] = source_branch
            if target_branch:
                where_clause["target_branch"] = target_branch
            if user_team_id:
                where_clause["user_team_id"] = user_team_id
            reviews = await ExtensionReviewsRepository.fetch_reviews_history(filters=where_clause)
            history = self.format_reviews(reviews)
            return history

        except Exception as e:  # noqa: BLE001
            AppLogger.log_error(f"Error fetching reviews: {str(e)}")
            return []

    @classmethod
    def format_reviews(cls, reviews: list[IdeReviewDTO]) -> list[dict]:
        formatted_reviews = []
        review_fields = {"id", "title", "execution_time_seconds", "review_datetime", "comments", "feedback"}
        feedback_fields = {"feedback_comment", "like"}
        comment_fields = {
            "id",
            "title",
            "comment",
            "corrective_code",
            "rationale",
            "file_path",
            "line_hash",
            "line_number",
            "tag",
            "comment_status",
            "feedback",
        }
        for review in reviews:
            review_data = review.model_dump(mode="json", include=review_fields)
            comments_per_agent = defaultdict(int)
            review_data["agent_summary"] = []
            agent_data = {}
            review_data["tag_summary"] = defaultdict(int)
            review_data["comments"] = defaultdict(list)
            review_data["feedback"] = (
                review.feedback.model_dump(mode="json", include=feedback_fields) if review.feedback else None
            )
            review_data["meta"] = {"file_count": 0, "comment_count": 0}
            for comment in review.comments:
                review_data["meta"]["comment_count"] += 1
                comment_data = comment.model_dump(mode="json", include=comment_fields)
                comment_data["feedback"] = (
                    comment.feedback.model_dump(mode="json", include=feedback_fields) if comment.feedback else None
                )
                comment_data["agent_ids"] = []
                for agent in comment.agents:
                    agent_data[agent.id] = {"name": agent.agent_name, "display_name": agent.display_name}
                    comments_per_agent[agent.id] += 1
                    comment_data["agent_ids"].append(agent.id)
                review_data["tag_summary"][comment.tag] += 1
                review_data["comments"][comment.file_path].append(comment_data)
            for key, count in comments_per_agent.items():
                review_data["agent_summary"].append(
                    {
                        "count": count,
                        "id": key,
                        "name": agent_data[key]["name"],
                        "display_name": agent_data[key]["display_name"],
                    }
                )
            for file in review.reviewed_files:
                if file not in review_data["comments"]:
                    review_data["comments"][file] = []
            review_data["meta"]["file_count"] = len(review_data["comments"])
            formatted_reviews.append(review_data)
        return formatted_reviews

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

            count = await DB.count_by_filters(model_name="dao.IdeReviews", filters=where_clause)

            return count

        except Exception as e:  # noqa: BLE001
            AppLogger.log_error(f"Error counting reviews: {str(e)}")
            return 0

    @classmethod
    async def update_comment_status(cls, comment_update_request: CommentUpdateRequest) -> Dict[str, str]:
        """Update the status of a comment."""
        try:
            comment = await IdeCommentRepository.db_get({"id": comment_update_request.id}, fetch_one=True)
            if not comment:
                raise ValueError(f"Comment with ID {comment_update_request.id} not found")

            await IdeCommentRepository.update_comment(
                comment_update_request.id, {"comment_status": comment_update_request.comment_status.value}
            )
            return {"message": "Comment updated successfully"}
        except Exception as e:
            AppLogger.log_error(f"Error updating comment status {comment_update_request.id}: {e}")
            raise e
