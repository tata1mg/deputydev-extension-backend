import asyncio
from typing import Any, Dict, List

from deputydev_core.utils.app_logger import AppLogger
from app.main.blueprints.deputy_dev.services.code_review.extension_review.base_websocket_manager import \
    BaseWebSocketManager
from app.main.blueprints.deputy_dev.services.code_review.extension_review.dataclass.main import WebSocketMessage
from app.main.blueprints.deputy_dev.services.code_review.extension_review.post_processors.extension_review_post_processor import (
    ExtensionReviewPostProcessor,
)


class PostProcessWebSocketManager(BaseWebSocketManager):
    """
    Manages post-process websocket communication for extension review.
    Handles streaming of post-processing results.
    """

    def __init__(self, connection_id: str, is_local: bool = False):
        super().__init__(connection_id, is_local)

    async def process_request(self, request_data: Dict[str, Any],
                              local_testing_stream_buffer: Dict[str, List[str]]) -> None:
        """
        Process post-process request and stream results.

        Args:
            request_data: Post-process request data
            local_testing_stream_buffer: Buffer for local testing
        """
        try:
            # Send start message
            await self.push_to_connection_stream(
                WebSocketMessage(
                    type="POST_PROCESS_START",
                    data={"message": "Post-processing started"}
                ),
                local_testing_stream_buffer
            )

            # Extract required data
            review_id = request_data.get("review_id")
            print("post process review id", request_data.get("user_team_id"))
            user_team_id = request_data.get("user_team_id")
            print("post process user team id", user_team_id)


            if not review_id:
                raise ValueError("review_id is required for post-processing")

            processor = ExtensionReviewPostProcessor()

            # Execute post processing
            result = await processor.post_process_pr(request_data, user_team_id=user_team_id)


            # Send completion message
            await self.push_to_connection_stream(
                WebSocketMessage(
                    type="POST_PROCESS_COMPLETE",
                    data={
                        "message": "Post-processing completed successfully",
                        "result": result or {"status": "SUCCESS"},
                        "progress": 100
                    }
                ),
                local_testing_stream_buffer
            )

        except Exception as e:
            AppLogger.log_error(f"Error in post-process request: {e}")
            await self.push_to_connection_stream(
                WebSocketMessage(
                    type="POST_PROCESS_ERROR",
                    data={"message": f"Post-processing failed: {str(e)}"}
                ),
                local_testing_stream_buffer
            )
        finally:
            # Send end message
            await self.push_to_connection_stream(
                WebSocketMessage(
                    type="STREAM_END",
                    data={"message": "Post-processing stream ended"}
                ),
                local_testing_stream_buffer
            )

    async def process_post_process_task(self, request_data: Dict[str, Any],
                                        local_testing_stream_buffer: Dict[str, List[str]]) -> None:
        """
        Background task to process post-process requests.

        Args:
            request_data: Post-process request data
            local_testing_stream_buffer: Buffer for local testing
        """
        try:
            await self.process_request(request_data, local_testing_stream_buffer)
        except Exception as e:
            AppLogger.log_error(f"Error in process_post_process_task: {e}")
            await self.send_error_message(f"Background task error: {str(e)}", local_testing_stream_buffer)
        finally:
            await self.cleanup()
