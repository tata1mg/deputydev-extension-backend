import json
from typing import Any

from sanic import Blueprint, response
from torpedo import Request


from app.main.blueprints.one_dev.utils.authenticate import authenticate
from app.main.blueprints.one_dev.utils.client.client_validator import validate_client_version
from app.main.blueprints.one_dev.utils.client.dataclasses.main import ClientData
from app.main.blueprints.one_dev.utils.dataclasses.main import AuthData


websocket_connection_v1_bp = Blueprint("websocket_connection_v1_bp", url_prefix="/websocket-connection")


@websocket_connection_v1_bp.post("/connect")
@validate_client_version
@authenticate
async def connect(_request: Request, client_data: ClientData, auth_data: AuthData, **kwargs: Any):
    print("Here")
    print("Headers: " + json.dumps(dict(_request.headers)))
    if _request.body:
        body_json = json.loads(_request.body.decode("utf-8"))
        print("Body: " + json.dumps(body_json))
    print("Query Params: " + json.dumps(dict(_request.args)))
    print("Connected")
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
