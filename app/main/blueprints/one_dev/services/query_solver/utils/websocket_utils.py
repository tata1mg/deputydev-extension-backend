import asyncio
import json

from sanic.server.websockets.impl import WebsocketImplProtocol


class WebSocketUtils:
    """Handle WebSocket utility operations for QuerySolver."""

    @staticmethod
    async def start_pinger(ws: WebsocketImplProtocol, interval: int = 25) -> None:
        """Start a background pinger task to keep WebSocket connection alive."""
        try:
            while True:
                await asyncio.sleep(interval)
                try:
                    await ws.send(json.dumps({"data": {"type": "PING"}}))
                except Exception:  # noqa: BLE001
                    break  # stop pinging if connection breaks
        except asyncio.CancelledError:
            pass
