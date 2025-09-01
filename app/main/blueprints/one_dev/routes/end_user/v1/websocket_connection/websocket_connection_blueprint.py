import asyncio
from typing import Any, Optional

from sanic import Blueprint, response
from sanic.response import JSONResponse

from app.backend_common.caches.websocket_connections_cache import (
    WebsocketConnectionCache,
)
from app.backend_common.utils.sanic_wrapper import Request
from app.main.blueprints.one_dev.utils.client.client_validator import (
    validate_client_headers_only,
)
from app.main.blueprints.one_dev.utils.client.dataclasses.main import ClientData
from app.main.blueprints.one_dev.utils.dataclasses.main import AuthData

websocket_connection_v1_bp = Blueprint("websocket_connection_v1_bp", url_prefix="/websocket-connection")


@websocket_connection_v1_bp.post("/connect")
@validate_client_headers_only
async def connect(_request: Request, client_data: ClientData, **kwargs: Any) -> JSONResponse:
    connectionid: str = _request.headers["connectionid"]
    auth_data: Optional[AuthData] = None
    auth_error: bool = False
    session_id: Optional[int] = None
    session_type: Optional[str] = None
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
async def disconnect(_request: Request) -> JSONResponse:
    connectionid: str = _request.headers["connectionid"]
    asyncio.create_task(WebsocketConnectionCache.delete([connectionid]))
    return response.json({"status": "SUCCESS"}, status=200)
