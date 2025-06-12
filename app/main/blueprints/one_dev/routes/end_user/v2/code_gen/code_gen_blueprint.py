import asyncio
import json
import uuid
import xxhash
from typing import Any, Dict, List, Optional
import httpx
from deputydev_core.utils.app_logger import AppLogger
from deputydev_core.utils.config_manager import ConfigManager
from sanic import Blueprint
from torpedo import Request, send_response
from app.backend_common.caches.websocket_connections_cache import (
    WebsocketConnectionCache,
)
from app.backend_common.caches.code_gen_tasks_cache import (
    CodeGenTasksCache,
)
from app.main.blueprints.one_dev.utils.cancellation_checker import (
    CancellationChecker,
)

from app.backend_common.models.dto.message_thread_dto import (
    ContentBlockCategory,
    MessageCallChainCategory,
    MessageThreadActor,
    MessageThreadData,
    MessageType,
    TextBlockContent,
    TextBlockData,
    LLModels,
)
from app.backend_common.repository.message_threads.repository import (
    MessageThreadsRepository,
)

from app.backend_common.repository.chat_attachments.repository import ChatAttachmentsRepository

from app.backend_common.service_clients.aws_api_gateway.aws_api_gateway_service_client import (
    AWSAPIGatewayServiceClient,
    SocketClosedException,
)
from app.backend_common.services.chat_file_upload.chat_file_upload import ChatFileUpload
from app.backend_common.services.llm.dataclasses.main import StreamingEventType
from app.main.blueprints.one_dev.services.query_solver.dataclasses.main import (
    InlineEditInput,
    QuerySolverInput,
    TerminalCommandEditInput,
    UserQueryEnhancerInput,
)
from app.main.blueprints.one_dev.services.query_solver.inline_editor import (
    InlineEditGenerator,
)
from app.main.blueprints.one_dev.services.query_solver.query_solver import QuerySolver
from app.main.blueprints.one_dev.services.query_solver.terminal_command_editor import (
    TerminalCommandEditGenerator,
)
from app.main.blueprints.one_dev.services.query_solver.user_query_enhancer import (
    UserQueryEnhancer,
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

from app.main.blueprints.one_dev.services.repository.query_summaries.query_summary_dto import (
    QuerySummarysRepository,
)
from app.main.blueprints.one_dev.models.dto.query_summaries import (
    QuerySummaryData,
)
from app.main.blueprints.one_dev.utils.version import compare_version


code_gen_v2_bp = Blueprint("code_gen_v2_bp", url_prefix="/code-gen")


local_testing_stream_buffer: Dict[str, List[str]] = {}


@code_gen_v2_bp.route("/generate-code-non-stream", methods=["POST"])
@validate_client_version
@authenticate
@ensure_session_id(auto_create=True)
async def solve_user_query_non_stream(
    _request: Request, client_data: ClientData, auth_data: AuthData, session_id: int, **kwargs: Any
):
    payload = QuerySolverInput(**_request.json, session_id=session_id)

    AppLogger.log_info(f"Starting new non-stream query for session {session_id}")

    # Clear any existing session cancellation state
    await CodeGenTasksCache.clear_session_cancellation(session_id)
    
    # Store the active query and LLM model for potential cancellation
    session_data = {}
    if payload.query:
        session_data["query"] = payload.query
    if payload.llm_model:
        session_data["llm_model"] = payload.llm_model.value
    if session_data:
        await CodeGenTasksCache._set_session_data(session_id, session_data)

    blocks = []

    # Add stream start block
    start_data = {"type": "STREAM_START"}
    if auth_data.session_refresh_token:
        start_data["new_session_data"] = auth_data.session_refresh_token
    blocks.append(start_data)

    # Create a task for this non-streaming request too for potential cancellation
    async def solve_query_task():
        checker = CancellationChecker(session_id)
        try:
            await checker.start_monitoring()
            try:
                data = await QuerySolver().solve_query(payload=payload, client_data=client_data)

                last_block = None
                async for data_block in data:
                    # Check if task was cancelled via Redis checker
                    if checker.is_cancelled():
                        blocks.append({"type": "STREAM_CANCELLED", "message": "LLM processing cancelled by session"})
                        raise asyncio.CancelledError("Task cancelled by session")

                    last_block = data_block
                    blocks.append(data_block.model_dump(mode="json"))

                if last_block and last_block.type != StreamingEventType.TOOL_USE_REQUEST_END:
                    blocks.append({"type": "QUERY_COMPLETE"})

                blocks.append({"type": "STREAM_END"})

            except asyncio.CancelledError:
                blocks.append({"type": "STREAM_CANCELLED", "message": "LLM processing cancelled"})
                raise
            except Exception as ex:
                AppLogger.log_error(f"Error in solving query: {ex}")
                blocks.append({"type": "STREAM_ERROR", "message": str(ex)})
            finally:
                # Clean up session data
                await CodeGenTasksCache.cleanup_session_data(session_id)
        finally:
            # Always stop monitoring
            try:
                await checker.stop_monitoring()
            except Exception:
                pass  # Ignore cleanup errors
        return blocks

    # Create and execute task without global tracking
    task = asyncio.create_task(solve_query_task())

    try:
        blocks = await task
    except asyncio.CancelledError:
        blocks.append({"type": "STREAM_CANCELLED", "message": "LLM processing cancelled"})

    return send_response({"status": "SUCCESS", "blocks": blocks})


@code_gen_v2_bp.route("/generate-code", methods=["POST"])
async def solve_user_query(_request: Request, **kwargs: Any):
    connection_id: str = _request.headers["connectionid"]
    connection_data: Any = await WebsocketConnectionCache.get(connection_id)
    if connection_data is None:
        raise ValueError(f"No connection data found for connection ID: {connection_id}")
    client_data = ClientData(**connection_data["client_data"])

    auth_error: bool
    auth_data: Optional[AuthData] = None
    _request.headers["Authorization"] = f"""Bearer {_request.json.get("auth_token", "")}"""
    _request.headers["X-Session-ID"] = str(_request.json.get("session_id", ""))
    _request.headers["X-Session-Type"] = str(_request.json.get("session_type", ""))
    auth_data: Optional[AuthData] = None
    auth_error: bool = False
    try:
        auth_data, _ = await get_auth_data(_request)
    except Exception:
        auth_error = True
        auth_data = None
    if auth_data:
        session_data = await get_valid_session_data(_request, client_data, auth_data, auto_create=True)
        _request.json["session_id"] = session_data.id
    is_local: bool = _request.headers.get("X-Is-Local") == "true"
    connection_id_gone = False
    aws_client = AWSAPIGatewayServiceClient()
    try:
        await aws_client.init_client(
            endpoint=f"{ConfigManager.configs['AWS_API_GATEWAY']['CODE_GEN_WEBSOCKET_WEBHOOK_ENDPOINT']}",
        )
    except asyncio.CancelledError:
        pass
    finally:
        await aws_client.close()

    async def push_to_connection_stream(data: Dict[str, Any]):
        nonlocal connection_id
        nonlocal is_local
        nonlocal connection_id_gone
        nonlocal aws_client

        if not connection_id_gone:
            if is_local:
                local_testing_stream_buffer.setdefault(connection_id, []).append(json.dumps(data))
            else:
                try:
                    await aws_client.post_to_connection(
                        connection_id=connection_id,
                        message=json.dumps(data),
                    )
                except SocketClosedException:
                    connection_id_gone = True

    if auth_error or not auth_data:
        error_data = {"type": "STREAM_ERROR", "message": "Unable to authenticate user", "status": "NOT_VERIFIED"}
        await push_to_connection_stream(error_data)
        return send_response({"status": "SESSION_EXPIRED"})

    user_team_id = auth_data.user_team_id
    payload_dict = _request.json
    if payload_dict.get("type") == "PAYLOAD_ATTACHMENT" and payload_dict.get("attachment_id"):
        attachment_id = payload_dict["attachment_id"]
        # 1. Lookup attachment
        attachment_data = await ChatAttachmentsRepository.get_attachment_by_id(attachment_id=attachment_id)

        if not attachment_data or getattr(attachment_data, "status", None) == "deleted":
            raise ValueError(f"Attachment with ID {attachment_id} not found or already deleted.")

        s3_key = attachment_data.s3_key

        # 2. Fetch & decode S3 payload
        try:
            object_bytes = await ChatFileUpload.get_file_data_by_s3_key(s3_key=s3_key)
            s3_payload = json.loads(object_bytes.decode("utf-8"))
        except Exception as e:
            raise ValueError(f"Failed to decode JSON payload from S3 for attachment {attachment_id}: {e}")

        # 3. Merge session fields from envelope (envelope wins)
        for field in ("session_id", "session_type", "auth_token"):
            if field in payload_dict:
                s3_payload[field] = payload_dict[field]
        payload_dict = s3_payload

        # 4. Delete S3 file and update DB (best effort; won't block downstream even if fails)
        try:
            await ChatFileUpload.delete_file_by_s3_key(s3_key=s3_key)
        except Exception as e:
            print(f"Warning: Failed to delete S3 payload file {s3_key}: {e}")

        try:
            await ChatAttachmentsRepository.update_attachment_status(
                attachment_id=attachment_id,
                status="deleted",
            )
        except Exception as e:
            print(f"Warning: Failed to mark attachment_id={attachment_id} as deleted in DB: {e}")

    payload = QuerySolverInput(
        **payload_dict,
        user_team_id=user_team_id,
    )


    # Clear any existing session cancellation state
    await CodeGenTasksCache.clear_session_cancellation(payload.session_id)

    AppLogger.log_info(f"Starting new stream query for session {payload.session_id}")

    # Store the active query and LLM model for potential cancellation
    session_data = {}
    if payload.query:
        session_data["query"] = payload.query
    if payload.llm_model:
        session_data["llm_model"] = payload.llm_model.value
    if session_data:
        await CodeGenTasksCache._set_session_data(payload.session_id, session_data)

    async def solve_query():
        nonlocal payload
        nonlocal connection_id
        nonlocal client_data

        current_session_id = payload.session_id if hasattr(payload, 'session_id') and payload.session_id else None

        # Use cancellation checker if we have a session_id
        checker = CancellationChecker(current_session_id) if current_session_id else None
        task_cancelled = False
        
        if checker:
            await checker.start_monitoring()

        try:
            # Mark session as active if we have session_id
            # push stream start message
            start_data = {"type": "STREAM_START"}
            if auth_data.session_refresh_token:
                start_data["new_session_data"] = auth_data.session_refresh_token
            await push_to_connection_stream(start_data)
            data = await QuerySolver().solve_query(payload=payload, client_data=client_data)
            last_block = None
            # push data to stream
            async for data_block in data:
                # Check if task was cancelled via Redis checker
                if checker and checker.is_cancelled():
                    task_cancelled = True
                    raise asyncio.CancelledError("Task cancelled by session")
                    
                if task_cancelled:
                    break
                    
                last_block = data_block
                await push_to_connection_stream(data_block.model_dump(mode="json"))

            # TODO: Sugar code this part
            if last_block and last_block.type != StreamingEventType.TOOL_USE_REQUEST_END:
                query_end_data = {"type": "QUERY_COMPLETE"}
                await push_to_connection_stream(query_end_data)

            # push stream end message
            end_data = {"type": "STREAM_END"}
            await push_to_connection_stream(end_data)
            
                
        except asyncio.CancelledError:
            cancel_data = {"type": "STREAM_CANCELLED", "message": "LLM processing cancelled "}
            await push_to_connection_stream(cancel_data)
            raise
        except Exception as ex:
            # push error message to stream
            error_data = {"type": "STREAM_ERROR", "message": f"LLM processing error: {str(ex)}"}
            await push_to_connection_stream(error_data)
        finally:
            await CodeGenTasksCache.cleanup_session_data(payload.session_id)
            # Stop the cancellation checker
            try:
                if checker:
                    await checker.stop_monitoring()
            except Exception:
                pass  
            
            await aws_client.close()

    task = asyncio.create_task(solve_query())
    
    # Store task data in Redis for session tracking
    current_session_id = payload.session_id if hasattr(payload, 'session_id') and payload.session_id else None
    
    return send_response({"status": "SUCCESS"})


@code_gen_v2_bp.route("/generate-enhanced-user-query", methods=["POST"])
@validate_client_version
@authenticate
@ensure_session_id(auto_create=True)
async def generate_enhanced_user_query(_request: Request, session_id: int, **kwargs: Any):
    input_data = UserQueryEnhancerInput(**_request.json, session_id=session_id)

    result = await UserQueryEnhancer().get_enhanced_user_query(
        payload=input_data,
    )

    return send_response(result, headers=kwargs.get("response_headers"))


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


@code_gen_v2_bp.route("/terminal-command-edit", methods=["POST"])
@validate_client_version
@authenticate
@ensure_session_id(auto_create=False)
async def terminal_command_edit(
    _request: Request, client_data: ClientData, auth_data: AuthData, session_id: int, **kwargs: Any
):
    input_data = TerminalCommandEditInput(**_request.json, session_id=session_id, auth_data=auth_data)
    result = await TerminalCommandEditGenerator().get_new_terminal_command(
        payload=input_data,
        client_data=client_data,
    )
    return send_response(result)




@code_gen_v2_bp.route("/cancel", methods=["POST"])
@validate_client_version
@authenticate
@ensure_session_id(auto_create=False)
async def cancel_chat(
    _request: Request, client_data: ClientData, auth_data: AuthData, session_id: int, **kwargs: Any
):
    # Mark session as cancelled in Redis - the cancellation checker will detect this
    await CodeGenTasksCache.cancel_session(session_id)

    # Get the stored active query and LLM model in a single call
    original_query, stored_llm_model = await CodeGenTasksCache.get_session_query_and_llm_model(session_id)
    cancelled_query_id = None

    if original_query:
        try:
            llm_model = LLModels(stored_llm_model)
            # Create the cancelled query message
            cancelled_query = f"[CANCELLED] {original_query}"

            # Create message thread data for the cancelled query
            data_hash = xxhash.xxh64(cancelled_query).hexdigest()
            message_data = [
                TextBlockData(
                    type=ContentBlockCategory.TEXT_BLOCK,
                    content=TextBlockContent(text=cancelled_query),
                    content_vars={"query": cancelled_query},
                )
            ]

            message_thread = MessageThreadData(
                session_id=session_id,
                actor=MessageThreadActor.USER,
                query_id=None,
                message_type=MessageType.QUERY,
                conversation_chain=[],
                message_data=message_data,
                data_hash=data_hash,
                prompt_type="CODE_QUERY_SOLVER",
                prompt_category="CODE_GENERATION",
                llm_model=llm_model,
                call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
            )

            created_thread = await MessageThreadsRepository.create_message_thread(message_thread)
            query_id = created_thread.id

            await QuerySummarysRepository.create_query_summary(
                QuerySummaryData(
                    session_id=session_id,
                    query_id=query_id,
                    summary=cancelled_query,
                )
            )

        except Exception as ex:
            AppLogger.log_error(f"Error creating cancelled query entry: {ex}")
            return None

    
    return send_response({
        "status": "SUCCESS", 
        "message": "LLM processing cancelled successfully ⚡",
        "cancelled_query_id": cancelled_query_id,
        "cancelled_session_id": session_id,
    })





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

            while True:
                try:
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
                                # del local_testing_stream_buffer[connection_id]
                                break
                        else:
                            await asyncio.sleep(0.2)
                except Exception as e:
                    AppLogger.log_error(f"Error in websocket connection: {e}")
                    break

            # finally, disconnect from the server using /disconnect endpoint
            # await client.post(
            #     f"{self_host_url}/end_user/v1/websocket-connection/disconnect", headers={"connectionid": connection_id}
            # )
    except Exception as _ex:
        AppLogger.log_error(f"Error in websocket connection: {_ex}")
