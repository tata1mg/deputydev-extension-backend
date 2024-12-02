from torpedo import CONFIG

from app.main.blueprints.deputy_dev.caches.affirmation import AffirmationCache
from app.main.blueprints.deputy_dev.constants.constants import (
    PR_REVIEW_POST_AFFIRMATION_MESSAGES,
    PrStatusTypes,
)
from app.main.blueprints.deputy_dev.services.comment.base_comment import BaseComment

config = CONFIG.config


class AffirmationService:
    def __init__(self, data: dict, comment_service: BaseComment):

        self.comment_service = comment_service
        self.cache_key = (
            f"AFFIRMATION_COMMENT_{data['workspace']}_{data['repo_name']}_{data['pr_id']}_{data['request_id']}"
        )

    async def get_comment_id(self) -> str:
        """Get affirmation comment ID from cache"""
        affirmation_details = await AffirmationCache.get(self.cache_key)
        return affirmation_details.get("comment_id") if affirmation_details else None

    async def create_affirmation_reply(self, review_status: str, commit_id: str = None) -> None:
        """
        Create a reply to the affirmation comment

        Args:
            review_status: Status message type from PrStatusTypes
            commit_id: Optional commit ID for formatting message
        """
        comment_id = await self.get_comment_id()

        message = PR_REVIEW_POST_AFFIRMATION_MESSAGES[review_status].format(commit_id=commit_id)

        if comment_id:
            response = await self.comment_service.create_comment_on_parent(
                comment=message, parent_id=comment_id, model=config.get("FEATURE_MODELS").get("PR_REVIEW")
            )
        else:
            response = await self.comment_service.create_pr_comment(
                comment=message, model=config.get("FEATURE_MODELS").get("PR_REVIEW")
            )

        if response and response.status_code in [200, 201]:
            await self.clear_cache()

    async def clear_cache(self) -> None:
        """Clear the affirmation comment cache"""
        await AffirmationCache.delete([self.cache_key])

    async def create_initial_comment(self) -> None:
        """Create initial affirmation comment and store its ID in cache"""
        comment_response = await self.comment_service.create_pr_comment(
            PR_REVIEW_POST_AFFIRMATION_MESSAGES[PrStatusTypes.IN_PROGRESS.value],
            config.get("FEATURE_MODELS").get("PR_REVIEW"),
        )

        if comment_response and comment_response.status_code in [200, 201]:
            comment_details = {"comment_id": comment_response.json()["id"]}
            await AffirmationCache.set(self.cache_key, comment_details)
