from typing import Any

from sanic import Blueprint
from sanic.response import JSONResponse

from app.backend_common.utils.sanic_wrapper import CONFIG, Request, send_response
from app.backend_common.utils.sanic_wrapper.types import ResponseDict
from app.main.blueprints.deputy_dev.services.setting.setting_service import (
    SettingService,
)

setting = Blueprint("setting", "/setting")

config = CONFIG.config


@setting.route("/team_setting", methods=["POST"])
async def create_org_setting(_request: Request, **kwargs: Any) -> ResponseDict | JSONResponse:
    payload = _request.custom_json()
    query_params = _request.request_params()
    await SettingService.create_or_update_team_settings(payload, query_params=query_params)
    return send_response("Success")
