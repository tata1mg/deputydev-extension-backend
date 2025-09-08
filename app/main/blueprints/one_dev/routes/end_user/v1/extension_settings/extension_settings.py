from typing import Any

from sanic import Blueprint
from sanic.response import JSONResponse

from app.backend_common.utils.authenticate import authenticate
from app.backend_common.utils.dataclasses.main import (
    AuthData,
    ClientData,
)
from app.backend_common.utils.sanic_wrapper import CONFIG, Request, send_response
from app.backend_common.utils.sanic_wrapper.exceptions import BadRequestException, HTTPRequestException
from app.backend_common.utils.sanic_wrapper.response import ResponseDict
from app.main.blueprints.one_dev.models.dto.extension_settings_dto import (
    ExtensionSettingsData,
    Settings,
)
from app.main.blueprints.one_dev.services.repository.extension_settings.repository import (
    ExtensionSettingsRepository,
)
from app.main.blueprints.one_dev.utils.client.client_validator import (
    validate_client_version,
)

extension_settings_v1_bp = Blueprint("extension_settings_v1_bp", url_prefix="/extension_settings")


@extension_settings_v1_bp.route("/update_extension_settings", methods=["POST"])
@validate_client_version
@authenticate
async def update_extension_settings(
    _request: Request, client_data: ClientData, auth_data: AuthData, **kwargs: Any
) -> ResponseDict | JSONResponse:
    try:
        settings_dict = _request.json
        if not settings_dict:
            raise BadRequestException("Settings not found in request")

        await ExtensionSettingsRepository.update_or_create_extension_settings(
            ExtensionSettingsData(
                user_team_id=auth_data.user_team_id, client=client_data.client, settings=Settings(**settings_dict)
            )
        )
    except Exception as e:  # noqa: BLE001
        raise HTTPRequestException(f"Failed to update extension settings: {str(e)}")
    return send_response({"message": "Extension settings updated successfully"}, headers=kwargs.get("response_headers"))


@extension_settings_v1_bp.route("/get_extension_settings", methods=["GET"])
@validate_client_version
@authenticate
async def get_extension_settings(_request: Request, auth_data: AuthData, **kwargs: Any) -> ResponseDict | JSONResponse:
    try:
        response = await ExtensionSettingsRepository.get_extension_settings_by_user_team_id(auth_data.user_team_id)
        if response is None:
            settings = CONFIG.config["DEFAULT_EXTENSION_SETTINGS"]
        else:
            settings = response.settings.model_dump(mode="json")
    except Exception as e:  # noqa: BLE001
        raise HTTPRequestException(f"Failed to get extension settings: {str(e)}")
    return send_response(settings, headers=kwargs.get("response_headers"))
