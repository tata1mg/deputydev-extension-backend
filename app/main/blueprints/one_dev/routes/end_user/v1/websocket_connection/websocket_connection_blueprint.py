import asyncio
from typing import Any, Optional

from sanic import Blueprint, response
from torpedo import Request

from app.backend_common.caches.websocket_connections_cache import (
    WebsocketConnectionCache,
)
from app.main.blueprints.one_dev.utils.client.client_validator import (
    validate_client_version,
)
from app.main.blueprints.one_dev.utils.client.dataclasses.main import ClientData

websocket_connection_v1_bp = Blueprint("websocket_connection_v1_bp", url_prefix="/websocket-connection")


@websocket_connection_v1_bp.post("/connect")
@validate_client_version
async def connect(_request: Request, client_data: ClientData, **kwargs: Any):
    connectionid: str = _request.headers["connectionid"]

    await WebsocketConnectionCache.set(
        key=connectionid,
        value={
            "client_data": client_data.model_dump(mode="json"),
        },
    )
    return response.json({"status": "SUCCESS"}, status=200)


@websocket_connection_v1_bp.post("/disconnect")
async def disconnect(_request: Request):
    connectionid: str = _request.headers["connectionid"]
    asyncio.create_task(WebsocketConnectionCache.delete([connectionid]))
    return response.json({"status": "SUCCESS"}, status=200)
