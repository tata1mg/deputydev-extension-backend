import asyncio
from typing import Any

from sanic import Blueprint, response
from torpedo import Request

from app.backend_common.caches.websocket_connections_cache import (
    WebsocketConnectionCache,
)
from app.main.blueprints.one_dev.utils.authenticate import authenticate
from app.main.blueprints.one_dev.utils.client.client_validator import (
    validate_client_version,
)
from app.main.blueprints.one_dev.utils.client.dataclasses.main import ClientData
from app.main.blueprints.one_dev.utils.dataclasses.main import AuthData
from app.main.blueprints.one_dev.utils.session import ensure_session_id

websocket_connection_v1_bp = Blueprint("websocket_connection_v1_bp", url_prefix="/websocket-connection")


@websocket_connection_v1_bp.post("/connect")
@validate_client_version
@authenticate
@ensure_session_id(auto_create=True)
async def connect(_request: Request, client_data: ClientData, auth_data: AuthData, session_id: int, **kwargs: Any):
    connectionid: str = _request.headers["connectionid"]
    session_type: str = _request.headers["x-session-type"]
    await WebsocketConnectionCache.set(
        key=connectionid,
        value={
            "session_id": session_id,
            "client_data": client_data.model_dump(mode="json"),
            "auth_data": auth_data.model_dump(mode="json"),
            "session_type": session_type,
        },
    )
    return response.json({"status": "SUCCESS"}, status=200)


@websocket_connection_v1_bp.post("/disconnect")
async def disconnect(_request: Request):
    connectionid: str = _request.headers["connectionid"]
    asyncio.create_task(WebsocketConnectionCache.delete([connectionid]))
    return response.json({"status": "SUCCESS"}, status=200)
