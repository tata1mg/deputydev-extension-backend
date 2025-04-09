import asyncio
import json
import uuid
from typing import Any, Dict, List

import httpx
from deputydev_core.utils.app_logger import AppLogger
from deputydev_core.utils.config_manager import ConfigManager
from sanic import Blueprint
from torpedo import Request, send_response

from app.backend_common.caches.websocket_connections_cache import (
    WebsocketConnectionCache,
)
from app.backend_common.service_clients.aws_api_gateway.aws_api_gateway_service_client import (
    AWSAPIGatewayServiceClient,
    SocketClosedException,
)
from app.backend_common.services.llm.dataclasses.main import StreamingEventType
from app.main.blueprints.one_dev.services.query_solver.dataclasses.main import (
    InlineEditInput,
    QuerySolverInput,
)
from app.main.blueprints.one_dev.services.query_solver.inline_editor import (
    InlineEditGenerator,
)
from app.main.blueprints.one_dev.services.query_solver.query_solver import QuerySolver
from app.main.blueprints.one_dev.utils.authenticate import authenticate
from app.main.blueprints.one_dev.utils.client.client_validator import (
    validate_client_version,
)
from app.main.blueprints.one_dev.utils.client.dataclasses.main import ClientData
from app.main.blueprints.one_dev.utils.dataclasses.main import AuthData
from app.main.blueprints.one_dev.utils.session import ensure_session_id

code_gen_v2_bp = Blueprint("code_gen_v2_bp", url_prefix="/code-gen")


local_testing_stream_buffer: Dict[str, List[str]] = {}


@code_gen_v2_bp.route("/generate-code-non-stream", methods=["POST"])
@validate_client_version
@authenticate
@ensure_session_id(auto_create=True)
async def solve_user_query_non_stream(_request: Request, client_data: ClientData, auth_data: AuthData, session_id: int, **kwargs: Any):
    payload = QuerySolverInput(**_request.json, session_id=session_id)

    blocks = []

    # Add stream start block
    start_data = {"type": "STREAM_START"}
    if auth_data.session_refresh_token:
        start_data["new_session_data"] = auth_data.session_refresh_token
    blocks.append(start_data)

    try:
        data = await QuerySolver().solve_query(payload=payload, client_data= client_data)

        last_block = None
        async for data_block in data:
            last_block = data_block
            blocks.append(data_block.model_dump(mode="json"))

        if last_block and last_block.type != StreamingEventType.TOOL_USE_REQUEST_END:
            blocks.append({"type": "QUERY_COMPLETE"})

        blocks.append({"type": "STREAM_END"})

    except Exception as ex:
        AppLogger.log_error(f"Error in solving query: {ex}")
        blocks.append({"type": "STREAM_ERROR", "message": str(ex)})

    return send_response({"status": "SUCCESS", "blocks": blocks})


@code_gen_v2_bp.route("/generate-code", methods=["POST"])
async def solve_user_query(_request: Request, **kwargs: Any):
    connection_id: str = _request.headers["connectionid"]  # type: ignore

    connection_data: Any = await WebsocketConnectionCache.get(connection_id)
    auth_data = AuthData(**connection_data["auth_data"])
    client_data = ClientData(**connection_data["client_data"])
    session_id: int = connection_data["session_id"]

    payload = QuerySolverInput(**_request.json, session_id=session_id)
    is_local: bool = _request.headers.get("X-Is-Local") == "true"
    connection_id_gone = False

    async def push_to_connection_stream(data: Dict[str, Any]):
        nonlocal connection_id
        nonlocal is_local
        nonlocal connection_id_gone

        if not connection_id_gone:
            if is_local:
                local_testing_stream_buffer.setdefault(connection_id, []).append(json.dumps(data))
            else:
                try:
                    await AWSAPIGatewayServiceClient().post_to_endpoint_connection(
                        f"{ConfigManager.configs['AWS_API_GATEWAY']['CODE_GEN_WEBSOCKET_WEBHOOK_ENDPOINT']}",
                        connection_id=connection_id,
                        message=json.dumps(data),
                    )
                except SocketClosedException:
                    connection_id_gone = True

    async def solve_query():
        nonlocal payload
        nonlocal connection_id
        nonlocal client_data

        # push stream start message
        start_data = {"type": "STREAM_START"}
        if auth_data.session_refresh_token:
            start_data["new_session_data"] = auth_data.session_refresh_token
        await push_to_connection_stream(start_data)
        try:
            data = await QuerySolver().solve_query(payload=payload, client_data=client_data)

            last_block = None
            # push data to stream
            async for data_block in data:
                last_block = data_block
                await push_to_connection_stream(data_block.model_dump(mode="json"))

            # TODO: Sugar code this part
            if last_block and last_block.type != StreamingEventType.TOOL_USE_REQUEST_END:
                query_end_data = {"type": "QUERY_COMPLETE"}
                await push_to_connection_stream(query_end_data)

            # push stream end message
            end_data = {"type": "STREAM_END"}
            await push_to_connection_stream(end_data)
        except Exception as ex:
            AppLogger.log_error(f"Error in solving query: {ex}")

            # push error message to stream
            error_data = {"type": "STREAM_ERROR", "message": str(ex)}
            await push_to_connection_stream(error_data)

    asyncio.create_task(solve_query())
    return send_response({"status": "SUCCESS"})


@code_gen_v2_bp.route("/generate-inline-edit", methods=["POST"])
@validate_client_version
@authenticate
@ensure_session_id(auto_create=True)
async def generate_inline_edit(
    _request: Request, client_data: ClientData, auth_data: AuthData, session_id: int, **kwargs: Any
):
    data = await InlineEditGenerator().create_and_start_job(
        payload=InlineEditInput(**_request.json, session_id=session_id, auth_data=auth_data),
        client_data=client_data,
    )
    return send_response({"job_id": data, "session_id": session_id})


# This is for testing purposes only
# This mocks the AWS api gateway connection
@code_gen_v2_bp.websocket("/generate-code-local-connection")
async def sse_websocket(request: Request, ws: Any):
    try:
        async with httpx.AsyncClient() as client:
            # generate a random connectionid
            connection_id = uuid.uuid4().hex
            # first mock connecting to the server using /connect endpoint
            self_host_url = f"http://{ConfigManager.configs['HOST']}:{ConfigManager.configs['PORT']}"
            connection_response = await client.post(
                f"{self_host_url}/end_user/v1/websocket-connection/connect",
                headers={**dict(request.headers), "connectionid": connection_id},
            )
            connection_data = connection_response.json()
            if connection_data.get("status") != "SUCCESS":
                raise Exception("Connection failed")

            # now receive the data
            raw_payload = await ws.recv()
            payload = json.loads(raw_payload)

            # then get a stream of data from the /generate-code endpoint
            await client.post(
                f"{self_host_url}/end_user/v2/code-gen/generate-code",
                headers={"connectionid": connection_id, "X-Is-Local": "true"},
                json=payload,
            )

            # iterate over message response and send the data to the client
            while True:
                if local_testing_stream_buffer.get(connection_id):
                    data = local_testing_stream_buffer[connection_id].pop(0)
                    await ws.send(data)
                    if data == json.dumps({"type": "STREAM_END"}):
                        # remove the connectionid from stream buffer
                        del local_testing_stream_buffer[connection_id]
                        break
                else:
                    await asyncio.sleep(0.2)

            # finally, disconnect from the server using /disconnect endpoint
            await client.post(
                f"{self_host_url}/end_user/v1/websocket-connection/disconnect", headers={"connectionid": connection_id}
            )
    except Exception as _ex:
        AppLogger.log_error(f"Error in websocket connection: {_ex}")
