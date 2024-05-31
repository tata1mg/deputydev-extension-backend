from pydantic import ValidationError
from sanic.log import logger
from torpedo import CONFIG
from torpedo.exceptions import BadRequestException

from app.managers.bitbucket.webhook import WebhookManager
from app.models.http_requests.code_review_request import CodeReviewRequest
from app.sqs.genai_subscriber import GenaiSubscriber


class CodeReviewTrigger:
    """Triggers code review"""

    @classmethod
    async def perform_review(cls, payload: dict):
        """
        Triggers code review
        Args:
            payload (dict): payload from webhook or
        Returns:
            PR review acknowledgments
        """
        config = CONFIG.config
        # handling for call from webhook
        try:
            if payload.get("repository"):
                payload = WebhookManager.parse_deputy_dev_payload(payload)
            payload = CodeReviewRequest(**payload)
        except ValidationError as ex:
            logger.error(ex)
            raise BadRequestException(f"invalid request with error {ex.errors()}")

        if payload.repo_name not in config.get("BLOCKED_REPOS"):
            logger.info("Whitelisted request: {}".format(payload))
            await GenaiSubscriber(config=config).publish(payload=payload.dict())
            return f"Processing Started with PR ID : {payload.pr_id}"
        else:
            logger.info("Blocked request for service: {} with  PR ID: {}".format(payload.repo_name, payload.pr_id))
            return f"Currently we are not serving: {payload.repo_name}"
