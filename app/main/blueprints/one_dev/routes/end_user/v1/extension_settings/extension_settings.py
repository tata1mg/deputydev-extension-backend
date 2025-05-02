from typing import Any

from sanic import Blueprint
from torpedo import Request, send_response
from torpedo.exceptions import BadRequestException, HTTPRequestException
from app.main.blueprints.one_dev.models.dto.extension_settings_dto import ExtensionSettingsData, Settings
from app.main.blueprints.one_dev.services.repository.extension_settings.repository import ExtensionSettingsRepository
from app.main.blueprints.one_dev.utils.authenticate import authenticate
from app.main.blueprints.one_dev.utils.client.client_validator import (
    validate_client_version,
)
from app.main.blueprints.one_dev.utils.client.dataclasses.main import ClientData
from app.main.blueprints.one_dev.utils.dataclasses.main import AuthData
from app.main.blueprints.one_dev.utils.client.dataclasses.main import Clients

extension_settings_v1_bp = Blueprint("extension_settings_v1_bp", url_prefix="/extension_settings")


@extension_settings_v1_bp.route("/update_extension_settings", methods=["POST"])
@validate_client_version
@authenticate
async def update_extension_settings(_request: Request, client_data: ClientData, auth_data: AuthData, **kwargs: Any):
    try:
        settings_dict = _request.json.get("settings")
        if not settings_dict:
            raise BadRequestException("Settings not found in request")

        await ExtensionSettingsRepository.update_or_create_extension_settings(
            ExtensionSettingsData(
                user_team_id=auth_data.user_team_id,
                client=client_data.client,
                settings=Settings(**settings_dict)
            )
        )
    except Exception as e:
        raise HTTPRequestException(f"Failed to update extension settings: {str(e)}")
    return send_response({"message": "Extension settings updated successfully"}, headers=kwargs.get("response_headers"))

@extension_settings_v1_bp.route("/get_extension_settings", methods=["GET"])
@validate_client_version
@authenticate
async def get_extension_settings(_request: Request, auth_data: AuthData, **kwargs: Any):
    try:
        response = await ExtensionSettingsRepository.get_extension_settings_by_user_team_id(auth_data.user_team_id)
        if response is None:
            raise BadRequestException("Extension settings not found")
        settings = response.settings
    except Exception as e:
        raise HTTPRequestException(f"Failed to get extension settings: {str(e)}")
    return send_response(settings.model_dump(mode="json"), headers=kwargs.get("response_headers"))
