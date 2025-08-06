from datetime import datetime, timezone
from typing import Optional

from pydantic import ValidationError
from sanic.log import logger
from torpedo import CONFIG
from torpedo.exceptions import BadRequestException

from app.main.blueprints.deputy_dev.models.code_review_request import CodeReviewRequest
from app.main.blueprints.deputy_dev.services.comment.affirmation_comment_service import (
    AffirmationService,
)
from app.main.blueprints.deputy_dev.services.comment.comment_factory import (
    CommentFactory,
)
from app.main.blueprints.deputy_dev.services.message_queue.factories.message_queue_factory import (
    MessageQueueFactory,
)
from app.main.blueprints.deputy_dev.services.webhook.pr_webhook import PRWebhook
from app.main.blueprints.deputy_dev.utils import (
    get_vcs_auth_handler,
    is_request_from_blocked_repo,
    update_payload_with_jwt_data,
)
from app.main.blueprints.deputy_dev.services.code_review.vcs_review.pr_review_manager import (
    PRReviewManager,
)

config = CONFIG.config


class CodeReviewTrigger:
    """Triggers code review"""

    @classmethod
    async def __preprocess_review_payload(cls, payload: dict, query_params: dict) -> Optional[CodeReviewRequest]:
        """
        Internal method Preprocesses the payload, updates it with JWT data, and parses it if needed.
        Args:
            payload (dict): Payload from webhook or other source.
            query_params (dict): Request query params containing a JWT token.
        Returns:
            CodeReviewRequest: Parsed and validated code review request.
        Raises:
            BadRequestException: If payload validation fails.
        """
        payload = update_payload_with_jwt_data(query_params, payload)

        try:
            if not payload.get("development"):
                payload = await PRWebhook.parse_payload(payload)
            if not payload:
                return
            return CodeReviewRequest(**payload)
        except ValidationError as ex:
            logger.error(ex)
            raise BadRequestException(f"Invalid PR review request with error {ex.errors()}")

    @classmethod
    async def __process_review_request(cls, code_review_request: CodeReviewRequest, is_skipped_auto_review_request: bool):  # Private method
        """
        Validates the repository and pushes the request to the appropriate queue.
        Args:
            code_review_request (CodeReviewRequest): Parsed and validated code review request.
        Returns:
            str: Acknowledgment message indicating processing status.
        """
        if is_skipped_auto_review_request:
            await PRReviewManager.handle_non_reviewable_request(code_review_request.dict())
            return
        if not is_request_from_blocked_repo(code_review_request.repo_name):
            logger.info("Whitelisted request: {}".format(code_review_request))
            await cls.__notify_pr_review_initiation(code_review_request.dict())
            await MessageQueueFactory.genai_subscriber()(config=config).publish(payload=code_review_request.dict())
            return f"Processing Started with PR ID : {code_review_request.pr_id}"
        else:
            logger.info(
                "Blocked request for service: {} with PR ID: {}".format(
                    code_review_request.repo_name, code_review_request.pr_id
                )
            )
            return f"Currently we are not serving: {code_review_request.repo_name}"



    @classmethod
    async def perform_review(cls, payload: dict, query_params: dict, is_manual_review: bool = True):
        """
        Triggers code review
        Args:
            payload (dict): payload from webhook or
            query_params (dict): request query params: contains a jwt token
            is_manual_review (bool): if manual review
        Returns:
            PR review acknowledgments
        """
        is_skipped_auto_review_request = is_manual_review or config.get("AUTO_REVIEW_ENABLED")
        pr_review_start_time = datetime.now(timezone.utc)
        payload["pr_review_start_time"] = pr_review_start_time.isoformat()
        code_review_request = await cls.__preprocess_review_payload(payload, query_params)
        if not code_review_request:
            return

        return await cls.__process_review_request(code_review_request, is_skipped_auto_review_request)

    @classmethod
    async def __notify_pr_review_initiation(cls, payload: dict) -> None:  # Private method
        repo_name, pr_id, workspace, scm_workspace_id, repo_id, workspace_slug, vcs_type = (
            payload.get("repo_name"),
            payload.get("pr_id"),
            payload.get("workspace"),
            payload.get("workspace_id"),
            payload.get("repo_id"),
            payload.get("workspace_slug"),
            payload.get("vcs_type"),
        )
        auth_handler = await get_vcs_auth_handler(scm_workspace_id, vcs_type)
        comment_service = await CommentFactory.initialize(
            vcs_type=vcs_type,
            repo_name=repo_name,
            pr_id=pr_id,
            workspace=workspace,
            workspace_slug=workspace_slug,
            auth_handler=auth_handler,
            repo_id=repo_id,
        )

        affirmation_service = AffirmationService(payload, comment_service)
        await affirmation_service.create_initial_comment()
