import json
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
@ensure_session_id(session_type="CODE_GENERATION_V2")
async def connect(_request: Request, client_data: ClientData, auth_data: AuthData, session_id: int, **kwargs: Any):
    print("Here")
    print("Headers: " + json.dumps(dict(_request.headers)))
    if _request.body:
        body_json = json.loads(_request.body.decode("utf-8"))
        print("Body: " + json.dumps(body_json))
    print("Query Params: " + json.dumps(dict(_request.args)))
    connectionid = _request.headers.get("connectionid")
    print("Connected")
    await WebsocketConnectionCache.set(
        key=connectionid,
        value={
            "session_id": session_id,
            "client_data": client_data.model_dump(mode="json"),
            "auth_data": auth_data.model_dump(mode="json"),
        },
    )
    return response.json({"status": "SUCCESS"}, status=200)


@websocket_connection_v1_bp.post("/disconnect")
async def disconnect(_request: Request):
    print("Headers: " + json.dumps(dict(_request.headers)))
    if _request.body:
        body_json = json.loads(_request.body.decode("utf-8"))
        print("Body: " + json.dumps(body_json))
    print("Query Params: " + json.dumps(dict(_request.args)))
    print("Disconnected")
    return response.json({"status": "SUCCESS"}, status=200)
