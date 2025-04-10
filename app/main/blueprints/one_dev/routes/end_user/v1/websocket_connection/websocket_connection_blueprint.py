import asyncio
from typing import Any, Optional

from sanic import Blueprint, response
from torpedo import Request

from app.backend_common.caches.websocket_connections_cache import (
    WebsocketConnectionCache,
)
from app.main.blueprints.one_dev.utils.authenticate import authenticate, get_auth_data
from app.main.blueprints.one_dev.utils.client.client_validator import (
    validate_client_version,
)
from app.main.blueprints.one_dev.utils.client.dataclasses.main import ClientData
from app.main.blueprints.one_dev.utils.dataclasses.main import AuthData
from app.main.blueprints.one_dev.utils.session import (
    ensure_session_id,
    get_valid_session_data,
)

websocket_connection_v1_bp = Blueprint("websocket_connection_v1_bp", url_prefix="/websocket-connection")


@websocket_connection_v1_bp.post("/connect")
@validate_client_version
async def connect(_request: Request, client_data: ClientData, **kwargs: Any):
    connectionid: str = _request.headers["connectionid"]
    session_type: str = _request.headers["x-session-type"]

    auth_data: Optional[AuthData] = None
    auth_error: bool = False
    try:
        auth_data, _ = await get_auth_data(_request)
    except Exception:
        auth_error = True
        auth_data = None

    session_id: Optional[int] = None
    if auth_data:
        sesion_data = await get_valid_session_data(_request, client_data, auth_data, auto_create=True)
        session_id = sesion_data.id

    await WebsocketConnectionCache.set(
        key=connectionid,
        value={
            "session_id": session_id,
            "client_data": client_data.model_dump(mode="json"),
            "auth_data": auth_data.model_dump(mode="json") if auth_data else None,
            "session_type": session_type,
            "auth_error": auth_error,
        },
    )
    return response.json({"status": "SUCCESS"}, status=200)


@websocket_connection_v1_bp.post("/disconnect")
async def disconnect(_request: Request):
    connectionid: str = _request.headers["connectionid"]
    asyncio.create_task(WebsocketConnectionCache.delete([connectionid]))
    return response.json({"status": "SUCCESS"}, status=200)
