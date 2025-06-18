import asyncio
from typing import Any, Optional

from deputydev_core.utils.constants.enums import Clients
from sanic import Blueprint, response
from torpedo import Request

from app.backend_common.caches.websocket_connections_cache import (
    WebsocketConnectionCache,
)
from app.main.blueprints.one_dev.utils.authenticate import get_auth_data
from app.main.blueprints.one_dev.utils.client.client_validator import (
    validate_client_version,
)
from app.main.blueprints.one_dev.utils.client.dataclasses.main import ClientData
from app.main.blueprints.one_dev.utils.dataclasses.main import AuthData
from app.main.blueprints.one_dev.utils.session import get_valid_session_data
from app.main.blueprints.one_dev.utils.version import compare_version

websocket_connection_v1_bp = Blueprint("websocket_connection_v1_bp", url_prefix="/websocket-connection")


@websocket_connection_v1_bp.post("/connect")
@validate_client_version
async def connect(_request: Request, client_data: ClientData, **kwargs: Any):
    connectionid: str = _request.headers["connectionid"]
    auth_data: Optional[AuthData] = None
    auth_error: bool = False
    session_id: Optional[int] = None
    session_type: Optional[str] = None

    if client_data.client == Clients.VSCODE_EXT and compare_version(client_data.client_version, "3.0.0", "<"):
        session_type = _request.headers["x-session-type"] if "x-session-type" in _request.headers else None
        try:
            auth_data, _ = await get_auth_data(_request)
        except Exception:
            auth_error = True
            auth_data = None
        if auth_data:
            sesion_data = await get_valid_session_data(_request, client_data, auth_data, auto_create=True)
            session_id = sesion_data.id

    await WebsocketConnectionCache.set(
        key=connectionid,
        value={
            "client_data": client_data.model_dump(mode="json"),
            "session_id": session_id if session_id else None,
            "session_type": session_type if session_type else None,
            "auth_data": auth_data.model_dump(mode="json") if auth_data else None,
            "auth_error": auth_error,
        },
    )
    return response.json({"status": "SUCCESS"}, status=200)


@websocket_connection_v1_bp.post("/disconnect")
async def disconnect(_request: Request):
    connectionid: str = _request.headers["connectionid"]
    asyncio.create_task(WebsocketConnectionCache.delete([connectionid]))
    return response.json({"status": "SUCCESS"}, status=200)
