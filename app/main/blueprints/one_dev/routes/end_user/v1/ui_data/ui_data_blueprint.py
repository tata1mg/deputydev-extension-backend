from typing import Any

from sanic import Blueprint
from sanic.response import JSONResponse

from app.backend_common.utils.authenticate import authenticate
from app.backend_common.utils.dataclasses.main import AuthData
from app.backend_common.utils.sanic_wrapper import Request, send_response
from app.backend_common.utils.sanic_wrapper.exceptions import BadRequestException
from app.backend_common.utils.sanic_wrapper.response import ResponseDict
from app.main.blueprints.one_dev.services.ui_data.ui_data import UIProfile
from app.main.blueprints.one_dev.utils.client.client_validator import (
    validate_client_version,
)

ui_data_v1_bp = Blueprint("ui_data_v1_bp", url_prefix="/ui_data")


@ui_data_v1_bp.route("/profile_ui", methods=["GET"])
@validate_client_version
@authenticate
async def get_ui_profile(_request: Request, auth_data: AuthData, **kwargs: Any) -> ResponseDict | JSONResponse:
    query_params = _request.args
    try:
        response = await UIProfile.get_ui_profile(
            user_team_id=auth_data.user_team_id, session_type=query_params["session_type"][0]
        )
    except Exception as e:  # noqa: BLE001
        raise BadRequestException(f"Failed to fetch ui profile data: {str(e)}")
    return send_response(response, headers=kwargs.get("response_headers"))
