import asyncio
import json
from typing import Any, AsyncIterator, Dict, Optional, Union
from uuid import uuid4

from pydantic import BaseModel
from sanic.server.websockets.impl import WebsocketImplProtocol

from app.backend_common.caches.code_gen_tasks_cache import CodeGenTasksCache
from app.backend_common.utils.dataclasses.main import AuthData, ClientData
from app.main.blueprints.one_dev.services.query_solver.core.core_processor import CoreProcessor
from app.main.blueprints.one_dev.services.query_solver.dataclasses.main import (
    QuerySolverInput,
    QuerySolverResumeInput,
)
from app.main.blueprints.one_dev.services.query_solver.payload.payload_processor import PayloadProcessor
from app.main.blueprints.one_dev.services.query_solver.stream_handler.stream_handler import StreamHandler
from app.main.blueprints.one_dev.services.query_solver.utils.websocket_utils import WebSocketUtils
from app.main.blueprints.one_dev.utils.cancellation_checker import CancellationChecker


class QuerySolver:
    """Main QuerySolver class that orchestrates query processing using various components."""

    def __init__(self):
        self.payload_processor = PayloadProcessor()
        self.core_processor = CoreProcessor()

    @staticmethod
    async def start_pinger(ws: WebsocketImplProtocol, interval: int = 25) -> None:
        """Start a background pinger task to keep WebSocket connection alive."""
        return await WebSocketUtils.start_pinger(ws, interval)

    @staticmethod
    async def process_s3_payload(payload_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Process S3 attachment payload and return the processed payload."""
        return await PayloadProcessor.process_s3_payload(payload_dict)

    @staticmethod
    async def handle_session_data_caching(payload: QuerySolverInput) -> None:
        """Handle session data caching for the payload."""
        return await PayloadProcessor.handle_session_data_caching(payload)

    async def execute_query_processing(
        self,
        payload: Union[QuerySolverInput, QuerySolverResumeInput],
        client_data: ClientData,
        auth_data: AuthData,
        ws: WebsocketImplProtocol,
    ) -> None:
        """Execute the query processing and stream results."""
        task_checker = CancellationChecker(payload.session_id)
        try:
            await task_checker.start_monitoring()

            # Send stream start notification
            start_data = {"type": "STREAM_START"}
            if auth_data.session_refresh_token:
                start_data["new_session_data"] = auth_data.session_refresh_token
            await ws.send(json.dumps(start_data))

            # Handle different payload types
            if self.payload_processor.is_resume_payload(payload):
                # Resume case: get existing query_id and start from offset
                query_id = await self.start_query_solver(
                    payload=payload, client_data=client_data, task_checker=task_checker
                )
                # Get stream from specific offset if provided
                offset_id = payload.resume_offset_id or "0"
                stream_iterator = await self.get_stream(query_id, offset_id=offset_id)
            else:
                # Normal case: start new query processing
                query_id = await self.start_query_solver(
                    payload=payload, client_data=client_data, task_checker=task_checker
                )
                stream_iterator = await self.get_stream(query_id)

            # Stream events to client
            async for data_block in stream_iterator:
                event_data = data_block.model_dump(mode="json")
                await ws.send(json.dumps(event_data))

                # Handle session cleanup for specific events
                if event_data.get("type") == "QUERY_COMPLETE":
                    await CodeGenTasksCache.cleanup_session_data(payload.session_id)

        except Exception as ex:  # noqa: BLE001
            from deputydev_core.utils.app_logger import AppLogger
            AppLogger.log_error(f"Error in WebSocket solve_query: {ex}")
            await ws.send(json.dumps({"type": "STREAM_ERROR", "message": f"WebSocket error: {str(ex)}"}))
        finally:
            await task_checker.stop_monitoring()

    async def solve_query(
        self,
        payload: QuerySolverInput,
        client_data: ClientData,
        save_to_redis: bool = False,
        task_checker: Optional[CancellationChecker] = None,
    ) -> AsyncIterator[BaseModel]:
        """Main query solving logic delegated to CoreProcessor."""
        return await self.core_processor.solve_query(payload, client_data, save_to_redis, task_checker)

    async def start_query_solver(
        self,
        payload: Union[QuerySolverInput, QuerySolverResumeInput],
        client_data: ClientData,
        task_checker: Optional[CancellationChecker] = None,
    ) -> str:
        """
        Wrapper function that starts the query solver and handles streaming part.
        Returns the query_id which is used as stream_id for getting the stream.
        """
        # Check if this is a resume payload
        if self.payload_processor.is_resume_payload(payload):
            return await self.resume_stream(payload)

        # Normal payload - generate new query_id and start processing
        query_id = uuid4().hex

        # Start the query solving process in background
        asyncio.create_task(
            self.core_processor.solve_query_with_streaming(
                payload=payload,
                client_data=client_data,
                query_id=query_id,
                task_checker=task_checker,
            )
        )

        return query_id

    async def get_stream(self, query_id: str, offset_id: str = "0") -> AsyncIterator[BaseModel]:
        """
        Get the stream iterator from Redis stream using query_id as stream_id.
        """
        async for event in StreamHandler.stream_from(stream_id=query_id, offset_id=offset_id):
            yield event

    async def resume_stream(
        self,
        payload: Union[QuerySolverInput, QuerySolverResumeInput],
    ) -> str:
        """
        Resume an existing stream from a given checkpoint ID and query_id.
        """
        if not payload.resume_query_id:
            raise ValueError("resume_query_id is required for resuming a stream")

        # Return the same query_id for stream continuation
        return payload.resume_query_id
