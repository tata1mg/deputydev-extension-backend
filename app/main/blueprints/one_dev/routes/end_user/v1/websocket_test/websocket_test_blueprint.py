import asyncio
import json
import random
import time
from typing import Any, Set

from deputydev_core.utils.app_logger import AppLogger
from sanic import Blueprint

from app.backend_common.utils.sanic_wrapper import Request

websocket_test_v1_bp = Blueprint("websocket_test_v1_bp", url_prefix="/websocket-test")

active_connections: Set[Any] = set()


def generate_payload(kb_size: int, base_json: str) -> str:
    filler_size = (kb_size * 1024) - len(base_json.encode("utf-8"))
    filler = "A" * max(filler_size, 0)
    payload_dict = json.loads(base_json)
    payload_dict["filler"] = filler
    return json.dumps(payload_dict)


async def _process_messages(ws: Any, payload_kb: int) -> None:
    """Process incoming WebSocket messages."""
    try:
        async for message in ws:
            try:
                if isinstance(message, str):
                    try:
                        data = json.loads(message)
                        echo_response_base = {
                            "type": "echo",
                            "original_data": data,
                            "timestamp": time.time(),
                            "message": "Echo: Received JSON data",
                            "payload_info": {
                                "payload": None,
                                "echo_size_kb": payload_kb,
                                "original_size_bytes": len(message.encode("utf-8")),
                            },
                        }
                    except json.JSONDecodeError:
                        echo_response_base = {
                            "type": "echo",
                            "original_text": message,
                            "timestamp": time.time(),
                            "message": f"Echo: {message}",
                            "payload_info": {
                                "payload": None,
                                "echo_size_kb": payload_kb,
                                "original_size_bytes": len(message.encode("utf-8")),
                            },
                        }
                else:
                    echo_response_base = {
                        "type": "echo",
                        "message": f"Echo: Received binary data of length {len(message)}",
                        "timestamp": time.time(),
                        "payload_info": {
                            "payload": None,
                            "echo_size_kb": payload_kb,
                            "original_size_bytes": len(message),
                        },
                    }

                echo_response_str = json.dumps(echo_response_base)
                echo_response_base["payload_info"]["payload"] = echo_response_str
                echo_response_str = json.dumps(echo_response_base)

                if payload_kb > 0:
                    echo_response_str = generate_payload(payload_kb, echo_response_str)

                await ws.send(echo_response_str)
                AppLogger.log_info(f"Echoed message back to client with {payload_kb}KB payload")

            except (ConnectionError, OSError, RuntimeError) as e:
                AppLogger.log_error(f"Error processing message: {e}")
                error_response_base = {
                    "type": "error",
                    "message": f"Error processing your message: {str(e)}",
                    "timestamp": time.time(),
                    "payload_info": {"payload": None, "error_size_kb": payload_kb},
                }
                error_response_str = json.dumps(error_response_base)
                error_response_base["payload_info"]["payload"] = error_response_str
                error_response_str = json.dumps(error_response_base)

                if payload_kb > 0:
                    error_response_str = generate_payload(payload_kb, error_response_str)

                await ws.send(error_response_str)
    except (ConnectionError, OSError, RuntimeError) as e:
        # This can happen when the connection is closed
        AppLogger.log_info(f"Message processing ended: {e}")


@websocket_test_v1_bp.websocket("/connect")
async def websocket_test_endpoint(request: Request, ws: Any) -> None:
    try:
        payload_kb = int(request.args.get("payload_kb", 1))
        ping_payload_kb = int(request.args.get("ping_payload_kb", payload_kb))
        ping_interval_sec = float(request.args.get("ping_interval_sec", 1))
        ws_duration_sec = int(request.args.get("ws_duration_sec", 30))

        max_payload_kb = 1024
        payload_kb = min(max(payload_kb, 0), max_payload_kb)
        ping_payload_kb = min(max(ping_payload_kb, 0), max_payload_kb)

        active_connections.add(ws)
        AppLogger.log_info(
            f"New WebSocket client connected with payload_kb={payload_kb}, ping_payload_kb={ping_payload_kb}, "
            f"ping_interval_sec={ping_interval_sec}, ws_duration_sec={ws_duration_sec}"
        )

        # Start ping task
        ping_task = asyncio.create_task(_send_custom_pings(ws, ping_payload_kb, ping_interval_sec, ws_duration_sec))

        try:
            # Run message processing with timeout constraint
            await asyncio.wait_for(_process_messages(ws, payload_kb), timeout=ws_duration_sec)
        except asyncio.TimeoutError:
            AppLogger.log_info(f"WebSocket connection timed out after {ws_duration_sec} seconds")
        except (ConnectionError, OSError, RuntimeError) as e:
            AppLogger.log_info(f"WebSocket message processing ended: {e}")
        finally:
            # Cancel remaining tasks
            ping_task.cancel()

            try:
                await ping_task
            except asyncio.CancelledError:
                pass
            except (ConnectionError, OSError, RuntimeError) as e:
                AppLogger.log_error(f"Error cancelling ping task: {e}")

            # Force close the connection if still open
            if hasattr(ws, "transport") and ws.transport and not ws.transport.is_closing():
                try:
                    ws.transport.close()
                    AppLogger.log_info("WebSocket transport forcefully closed in finally block")
                except (AttributeError, RuntimeError, OSError) as close_error:
                    AppLogger.log_error(f"Error forcefully closing WebSocket: {close_error}")

    except (ConnectionError, OSError, RuntimeError) as e:
        AppLogger.log_error(f"WebSocket connection error: {e}")
    finally:
        if ws in active_connections:
            active_connections.remove(ws)
        AppLogger.log_info("WebSocket client disconnected")


async def _send_custom_pings(ws: Any, payload_kb: int, ping_interval_sec: float, ws_duration_sec: int) -> None:
    try:
        t0 = time.time()
        num_pings = int(ws_duration_sec // ping_interval_sec)
        random_offsets = [random.uniform(0, ping_interval_sec) for _ in range(num_pings)]
        send_times = [t0 + offset + (i * ping_interval_sec) for i, offset in enumerate(random_offsets)]

        for send_time in send_times:
            now = time.time()
            delay = send_time - now
            if delay > 0:
                await asyncio.sleep(delay)

            if hasattr(ws, "transport") and (not ws.transport or ws.transport.is_closing()):
                break

            ping_message_base = {
                "type": "ping",
                "message": "Server ping - connection alive",
                "timestamp": time.time(),
                "payload_info": {"payload": None, "ping_size_kb": payload_kb},
            }

            ping_message_str = json.dumps(ping_message_base)
            ping_message_base["payload_info"]["payload"] = ping_message_str
            ping_message_str = json.dumps(ping_message_base)

            if payload_kb > 0:
                ping_message_str = generate_payload(payload_kb, ping_message_str)

            try:
                await ws.send(ping_message_str)
                AppLogger.log_info(f"Sent ping at {time.time() - t0:.2f}s with {payload_kb}KB payload")
            except (ConnectionError, OSError, RuntimeError) as e:
                AppLogger.log_error(f"Failed to send ping: {e}")
                break

    except asyncio.CancelledError:
        AppLogger.log_info("Ping task cancelled")
    except (ConnectionError, OSError, RuntimeError) as e:
        AppLogger.log_error(f"Error in custom ping task: {e}")


@websocket_test_v1_bp.get("/status")
async def websocket_status(request: Request) -> dict:
    return {
        "status": "active",
        "active_connections": len(active_connections),
        "endpoint": "/end_user/v1/websocket-test/connect",
        "features": [
            "Randomized pings across user-defined intervals",
            "Echo back all received messages",
            "Auto-disconnect after user-defined duration",
            "JSON and plain text support",
            "Configurable payload sizes for load testing",
        ],
        "payload_options": {
            "payload_kb": "Size in KB for echo messages (default: 1, max: 1024)",
            "ping_payload_kb": "Size in KB for ping messages (default: same as payload_kb, max: 1024)",
            "ping_interval_sec": "Interval in seconds to distribute each ping randomly (default: 1)",
            "ws_duration_sec": "WebSocket duration in seconds (default: 30)",
        },
    }


@websocket_test_v1_bp.get("/")
async def websocket_info(request: Request) -> dict:
    return {
        "name": "WebSocket Test API",
        "description": "WebSocket server for testing connectivity, echo, and ping with configurable payload and timing.",
        "endpoints": {
            "websocket": "/end_user/v1/websocket-test/connect",
            "status": "/end_user/v1/websocket-test/status",
            "info": "/end_user/v1/websocket-test/",
        },
        "features": {
            "ping": "Server sends randomized pings over the duration with configurable interval",
            "echo": "Server echoes back all received messages",
            "auto_disconnect": "WebSocket closes automatically after given duration",
            "formats": ["JSON", "Plain text", "Binary data"],
            "payload_sizing": "Configurable payload sizes for load testing",
        },
        "usage": {
            "connect": "Connect to ws://your-host/end_user/v1/websocket-test/connect",
            "example": "ws://your-host/end_user/v1/websocket-test/connect?payload_kb=10&ping_payload_kb=5&ping_interval_sec=2&ws_duration_sec=60",
            "send_message": "Send any text or JSON message",
            "receive": "Server will echo your message and send pings at randomized intervals",
        },
        "query_parameters": {
            "payload_kb": {
                "description": "Size in KB for echo messages",
                "type": "integer",
                "default": 1,
                "range": "0-1024",
            },
            "ping_payload_kb": {
                "description": "Size in KB for ping messages",
                "type": "integer",
                "default": "same as payload_kb",
                "range": "0-1024",
            },
            "ping_interval_sec": {
                "description": "Random interval spacing between pings (spread within each second)",
                "type": "float",
                "default": 1,
            },
            "ws_duration_sec": {
                "description": "Duration of the WebSocket session in seconds",
                "type": "integer",
                "default": 30,
            },
        },
    }
