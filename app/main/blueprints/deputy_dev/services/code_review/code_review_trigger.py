from pydantic import ValidationError
from sanic.log import logger
from torpedo import CONFIG
from torpedo.exceptions import BadRequestException

from app.main.blueprints.deputy_dev.models.code_review_request import CodeReviewRequest
from app.main.blueprints.deputy_dev.services.sqs.genai_subscriber import GenaiSubscriber
from app.main.blueprints.deputy_dev.services.webhook.pr_webhook import PRWebhook
from app.main.blueprints.deputy_dev.utils import (
    is_request_from_blocked_repo,
    update_payload_with_jwt_data,
)


class CodeReviewTrigger:
    """Triggers code review"""

    @classmethod
    async def perform_review(cls, payload: dict, query_params: dict):
        """
        Triggers code review
        Args:
            payload (dict): payload from webhook or
            query_params (dict): request quaer params: contains a jwt token
        Returns:
            PR review acknowledgments
        """
        config = CONFIG.config
        payload = update_payload_with_jwt_data(query_params, payload)

        # handling for call from webhook
        try:
            if not payload.get("development"):
                payload = await PRWebhook.parse_payload(payload)
            if not payload:
                return
            payload = CodeReviewRequest(**payload)
        except ValidationError as ex:
            logger.error(ex)
            raise BadRequestException(f"invalid pr review request with error {ex.errors()}")

        if not is_request_from_blocked_repo(payload.repo_name):
            logger.info("Whitelisted request: {}".format(payload))
            await GenaiSubscriber(config=config).publish(payload=payload.dict())
            return f"Processing Started with PR ID : {payload.pr_id}"
        else:
            logger.info("Blocked request for service: {} with  PR ID: {}".format(payload.repo_name, payload.pr_id))
            return f"Currently we are not serving: {payload.repo_name}"
