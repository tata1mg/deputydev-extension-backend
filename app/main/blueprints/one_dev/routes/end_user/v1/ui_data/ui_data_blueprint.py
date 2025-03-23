from sanic import Blueprint
from torpedo import Request, send_response
from torpedo.exceptions import BadRequestException

from app.main.blueprints.one_dev.services.ui_data.ui_data import UIProfile
from app.main.blueprints.one_dev.utils.authenticate import authenticate
from app.main.blueprints.one_dev.utils.client.client_validator import (
    validate_client_version,
)

from app.main.blueprints.one_dev.utils.dataclasses.main import AuthData


ui_data_v1_bp = Blueprint("ui_data_v1_bp", url_prefix="/ui_data")


@ui_data_v1_bp.route("/profile", methods=["GET"])
@validate_client_version
@authenticate
async def get_ui_profile(_request: Request, **kwargs):
    try:
        response = await UIProfile.get_ui_profile(user_team_id=1)
    except Exception as e:
        raise BadRequestException(f"Failed to fetch ui profile data: {str(e)}")
    return send_response(response, headers=kwargs.get("response_headers"))