from pydantic import ValidationError
from sanic.log import logger
from torpedo import CONFIG
from torpedo.exceptions import BadRequestException

from app.main.blueprints.deputy_dev.models.code_review_request import CodeReviewRequest
from app.main.blueprints.deputy_dev.services.sqs.genai_subscriber import GenaiSubscriber
from app.main.blueprints.deputy_dev.services.webhook.pr_webhook import PRWebhook


class CodeReviewTrigger:
    """Triggers code review"""

    @classmethod
    async def perform_review(cls, payload: dict, vcs_type: str, prompt_version: str = "v1"):
        """
        Triggers code review
        Args:
            payload (dict): payload from webhook or
            vcs_type (str): vcs type
            prompt_version (str): prompt version
        Returns:
            PR review acknowledgments
        """
        config = CONFIG.config
        # handling for call from webhook
        try:
            if not payload.get("development"):
                payload = PRWebhook.parse_payload(payload, vcs_type)
            payload["prompt_version"] = prompt_version
            payload["vcs_type"] = vcs_type
            payload = CodeReviewRequest(**payload)
        except ValidationError as ex:
            logger.error(ex)
            raise BadRequestException(f"invalid pr review request with error {ex.errors()}")

        if payload.repo_name not in config.get("BLOCKED_REPOS"):
            logger.info("Whitelisted request: {}".format(payload))
            await GenaiSubscriber(config=config).publish(payload=payload.dict())
            return f"Processing Started with PR ID : {payload.pr_id}"
        else:
            logger.info("Blocked request for service: {} with  PR ID: {}".format(payload.repo_name, payload.pr_id))
            return f"Currently we are not serving: {payload.repo_name}"
