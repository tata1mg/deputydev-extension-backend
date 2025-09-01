from app.backend_common.utils.sanic_wrapper import CONFIG
from app.main.blueprints.deputy_dev.caches.affirmation import AffirmationCache
from app.main.blueprints.deputy_dev.constants.constants import (
    PR_REVIEW_POST_AFFIRMATION_MESSAGES,
)
from app.main.blueprints.deputy_dev.services.comment.base_comment import BaseComment

config = CONFIG.config


class AffirmationService:
    def __init__(self, data: dict, comment_service: BaseComment) -> None:
        self.comment_service = comment_service
        self.cache_key = (
            f"AFFIRMATION_COMMENT_{data['workspace']}_{data['repo_name']}_{data['pr_id']}_{data['request_id']}"
        )

    async def get_comment_id(self) -> str:
        """Get affirmation comment ID from cache"""
        affirmation_details = await AffirmationCache.get(self.cache_key)
        return affirmation_details.get("comment_id") if affirmation_details else None

    async def create_affirmation_reply(
        self, message_type: str, commit_id: str = None, additional_context: dict = None
    ) -> None:
        """
        Create a reply to the affirmation comment

        Args:
            message_type: Status message type from PrStatusTypes
            commit_id: Optional commit ID for formatting message
            additional_context: Additional context for message formatting
        """
        comment_id = await self.get_comment_id()

        message = PR_REVIEW_POST_AFFIRMATION_MESSAGES[message_type]

        format_args = {"commit_id": commit_id} if commit_id else {}
        if additional_context:
            format_args.update(additional_context)

        formatted_message = message.format(**format_args)

        if comment_id:
            response = await self.comment_service.create_comment_on_parent(
                comment=formatted_message, parent_id=comment_id, model=config.get("FEATURE_MODELS").get("PR_REVIEW")
            )
        else:
            response = await self.comment_service.create_pr_comment(
                comment=formatted_message, model=config.get("FEATURE_MODELS").get("PR_REVIEW")
            )

        if response and response.status_code in [200, 201]:
            await self.clear_cache()

    async def clear_cache(self) -> None:
        """Clear the affirmation comment cache"""
        await AffirmationCache.delete([self.cache_key])

    async def create_initial_comment(self, message: str) -> None:
        """Create initial affirmation comment and store its ID in cache"""
        comment_response = await self.comment_service.create_pr_comment(
            message,
            config.get("FEATURE_MODELS").get("PR_REVIEW"),
        )

        comment_response_json = await comment_response.json()
        if comment_response_json and comment_response.status_code in [200, 201]:
            comment_details = {"comment_id": comment_response_json["id"]}
            await AffirmationCache.set(self.cache_key, comment_details)
