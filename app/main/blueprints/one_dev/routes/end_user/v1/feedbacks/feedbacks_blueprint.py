from typing import Any

from sanic import Blueprint
from sanic.response import JSONResponse
from torpedo import Request, send_response
from torpedo.exceptions import BadRequestException
from torpedo.response import ResponseDict

from app.main.blueprints.one_dev.services.code_generation.feedback.main import (
    FeedbackService,
)
from app.main.blueprints.one_dev.utils.authenticate import authenticate
from app.main.blueprints.one_dev.utils.client.client_validator import (
    validate_client_version,
)
from app.main.blueprints.one_dev.utils.dataclasses.main import AuthData
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
