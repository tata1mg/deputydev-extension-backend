from typing import Any

from deputydev_core.utils.app_logger import AppLogger
from sanic import Blueprint
from sanic.response import JSONResponse
from torpedo import CONFIG, Request, send_response
from torpedo.types import ResponseDict

from app.backend_common.utils.authenticate import authenticate
from app.backend_common.utils.dataclasses.main import AuthData
from app.backend_common.utils.wrapper import exception_logger
from app.main.blueprints.deputy_dev.models.dto.ide_review_feedback_dto import IdeReviewFeedbackDTO
from app.main.blueprints.deputy_dev.models.ide_review_history_params import ReviewHistoryParams
from app.main.blueprints.deputy_dev.models.request.ide_review_feedback.ide_review_feedback_payload import (
    IdeReviewFeedbackPayload,
)
from app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager import (
    IdeReviewManager,
)
from app.main.blueprints.deputy_dev.services.code_review.ide_review.managers.ide_code_review_history_manager import (
    IdeCodeReviewHistoryManager,
)
from app.main.blueprints.deputy_dev.services.code_review.ide_review.pre_processors.ide_review_pre_processor import (
    IdeReviewPreProcessor,
)
from app.main.blueprints.deputy_dev.services.repository.ide_review_feedbacks.repository import (
    IdeReviewFeedbacksRepository,
)
from app.main.blueprints.one_dev.utils.client.client_validator import (
    validate_client_version,
)

ide_review = Blueprint("ide_review", "")

config = CONFIG.config


@ide_review.route("/history", methods=["GET"])
@validate_client_version
@authenticate
async def code_review_history(_request: Request, auth_data: AuthData, **kwargs: Any) -> ResponseDict | JSONResponse:
    """
    Get code review history based on filters
    Query parameters:
    - user_team_id: Filter by user team ID
    - source_branch: Filter by source branch
    - target_branch: Filter by target branch
    - repo_id: Filter by repository ID
    """
    # Extract query parameters
    query_params = _request.request_params()
    review_history_params = ReviewHistoryParams(**query_params, user_team_id=auth_data.user_team_id)

    # Initialize manager and fetch reviews
    history_manager = IdeCodeReviewHistoryManager()
    reviews = await history_manager.fetch_reviews_by_filters(review_history_params)
    return send_response(reviews)


@ide_review.route("/pre-process", methods=["POST"])
@validate_client_version
@authenticate
async def pre_process_extension_review(
    request: Request, auth_data: AuthData, **kwargs: Any
) -> ResponseDict | JSONResponse:
    data = request.json
    processor = IdeReviewPreProcessor()
    review_dto = await processor.pre_process_pr(
        data,
        user_team_id=auth_data.user_team_id,
    )
    return send_response(review_dto)


@ide_review.route("/cancel_review", methods=["GET"])
@validate_client_version
@authenticate
async def cancel_review(request: Request, auth_data: AuthData, **kwargs: Any) -> ResponseDict | JSONResponse:
    """
    Generate a query to fix a specific comment in the code review.

    Query parameters:
    - comment_id: The ID of the comment to fix
    """
    try:
        query_params = request.request_params()
        review_id = query_params.get("review_id")
        if not review_id:
            raise ValueError("Missing required parameters: review_id")

        # Generate the fix query
        manager = IdeReviewManager()
        data = await manager.cancel_review(review_id=review_id)
        return send_response(data)
    except Exception as e:  # noqa: BLE001
        AppLogger.log_error(f"Error generating fix query: {e}")
        return send_response({"status": "ERROR", "message": str(e)})


@ide_review.route("/reviews/<review_id:int>/feedback", methods=["POST"])
@validate_client_version
@authenticate
@exception_logger
async def create_review_feedback(
    request: Request, auth_data: AuthData, review_id: int, **kwargs: Any
) -> ResponseDict | JSONResponse:
    """
    Create feedback for a specific review

    Request Body:
    {
        "feedback_comment": "string (optional)",
        "like": "boolean (optional)"
    }
    """
    # Get request body
    request_data = request.json or {}
    payload = IdeReviewFeedbackPayload(**request_data)
    # Create feedback DTO
    feedback_dto = IdeReviewFeedbackDTO(
        review_id=review_id, feedback_comment=payload.feedback_comment, like=payload.like
    )

    # Insert feedback via repository
    created_feedback = await IdeReviewFeedbacksRepository.db_insert(feedback_dto)

    return send_response(created_feedback.model_dump(mode="json"))
