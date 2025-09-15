from typing import Any

from sanic import Blueprint
from sanic.response import JSONResponse

from app.backend_common.utils.authenticate import authenticate
from app.backend_common.utils.dataclasses.main import AuthData
from app.backend_common.utils.sanic_wrapper import Request, send_response
from app.backend_common.utils.sanic_wrapper.exceptions import BadRequestException
from app.backend_common.utils.sanic_wrapper.response import ResponseDict
from app.main.blueprints.one_dev.services.feedback.feedback_service import FeedbackService
from app.main.blueprints.one_dev.utils.client.client_validator import (
    validate_client_version,
)
from app.main.blueprints.one_dev.utils.session import ensure_session_id

feedbacks_v1_bp = Blueprint("feedbacks_v1_bp", url_prefix="/feedbacks")


@feedbacks_v1_bp.route("/submit", methods=["POST"])
@validate_client_version
@authenticate
@ensure_session_id(auto_create=False)
async def submit_feedback(
    _request: Request, auth_data: AuthData, session_id: int, **kwargs: Any
) -> ResponseDict | JSONResponse:
    try:
        query_id = _request.headers.get("X-Query-ID")
        feedback = _request.headers.get("X-Feedback")
        user_team_id = auth_data.user_team_id

        response = await FeedbackService.record_extension_feedback(
            query_id=query_id, feedback=feedback, session_id=session_id, user_team_id=user_team_id
        )
    except Exception as e:  # noqa: BLE001
        raise BadRequestException(f"Failed to submit feedback: {str(e)}")
    return send_response(response, headers=kwargs.get("response_headers"))
