from typing import Any

from deputydev_core.utils.app_logger import AppLogger
from sanic import Blueprint
from sanic.response import JSONResponse
from torpedo import CONFIG, Request, send_response
from torpedo.types import ResponseDict

from app.backend_common.utils.authenticate import authenticate
from app.backend_common.utils.dataclasses.main import AuthData
from app.backend_common.utils.wrapper import exception_logger
from app.main.blueprints.deputy_dev.models.dto.ide_review_comment_feedback_dto import IdeReviewCommentFeedbackDTO
from app.main.blueprints.deputy_dev.models.request.ide_review_feedback.ide_review_comment_feedback_payload import (
    IdeReviewCommentFeedbackPayload,
)
from app.main.blueprints.deputy_dev.services.code_review.ide_review.dataclass.main import CommentUpdateRequest
from app.main.blueprints.deputy_dev.services.code_review.ide_review.ide_review_manager import IdeReviewManager
from app.main.blueprints.deputy_dev.services.code_review.ide_review.managers.ide_code_review_history_manager import (
    IdeCodeReviewHistoryManager,
)
from app.main.blueprints.deputy_dev.services.repository.ide_review_comment_feedbacks.repository import (
    IdeReviewCommentFeedbacksRepository,
)
from app.main.blueprints.one_dev.utils.client.client_validator import validate_client_version

comments = Blueprint("comments", "/comments")

config = CONFIG.config


@comments.route("/<comment_id:int>/feedback", methods=["POST"])
@validate_client_version
@authenticate
@exception_logger
async def create_comment_feedback(
    request: Request, auth_data: AuthData, comment_id: int, **kwargs: Any
) -> JSONResponse | ResponseDict:
    """
    Create feedback for a specific comment

    Request Body:
    {
        "feedback_comment": "string (optional)",
        "like": "boolean (optional)"
    }
    """
    request_data = request.json or {}
    payload = IdeReviewCommentFeedbackPayload(**request_data)
    feedback_dto = IdeReviewCommentFeedbackDTO(
        comment_id=comment_id, feedback_comment=payload.feedback_comment, like=payload.like
    )
    created_feedback = await IdeReviewCommentFeedbacksRepository.db_insert(feedback_dto)
    return send_response(created_feedback.model_dump(mode="json"))


@comments.route("/update-comment-status", methods=["POST"])
@validate_client_version
@authenticate
async def update_comment_status(request: Request, auth_data: AuthData, **kwargs: Any) -> JSONResponse | ResponseDict:
    """
    Generate a query to fix a specific comment in the code review.

    Query parameters:
    - comment_id: The ID of the comment to fix
    """
    try:
        query_params = request.request_params()
        comment_id = query_params.get("comment_id")
        status = query_params.get("status")
        comment_update_request = CommentUpdateRequest(id=comment_id, comment_status=status)
        if not comment_id:
            raise ValueError("Missing required parameters: comment_id")

        # Generate the fix query
        manager = IdeCodeReviewHistoryManager()
        data = await manager.update_comment_status(comment_update_request)
        return send_response(data)
    except Exception as e:  # noqa: BLE001
        AppLogger.log_error(f"Error updating comment status: {e}")
        return send_response({"status": "ERROR", "message": str(e)})


@comments.route("/generate-fix-query", methods=["GET"])
@validate_client_version
@authenticate
async def generate_comment_fix_query(
    request: Request, auth_data: AuthData, **kwargs: Any
) -> JSONResponse | ResponseDict:
    """
    Generate a query to fix a specific comment in the code review.

    Query parameters:
    - comment_id: The ID of the comment to fix
    """
    try:
        query_params = request.request_params()
        comment_id = query_params.get("comment_id")
        if not comment_id:
            raise ValueError("Missing required parameters: comment_id")

        # Generate the fix query
        manager = IdeReviewManager()
        fix_query = await manager.generate_comment_fix_query(comment_id=comment_id)
        return send_response({"fix_query": fix_query})
    except Exception as e:  # noqa: BLE001
        AppLogger.log_error(f"Error generating fix query: {e}")
        return send_response({"status": "ERROR", "message": str(e)})
