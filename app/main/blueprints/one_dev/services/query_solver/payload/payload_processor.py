import json
from typing import Any, Dict, Union

from deputydev_core.utils.app_logger import AppLogger

from app.backend_common.caches.code_gen_tasks_cache import CodeGenTasksCache
from app.backend_common.repository.chat_attachments.repository import ChatAttachmentsRepository
from app.backend_common.services.chat_file_upload.chat_file_upload import ChatFileUpload
from app.main.blueprints.one_dev.services.query_solver.dataclasses.main import (
    QuerySolverInput,
    QuerySolverResumeInput,
)


class PayloadProcessor:
    """Handle payload processing operations for QuerySolver."""

    @staticmethod
    async def process_s3_payload(payload_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Process S3 attachment payload and return the processed payload."""
        attachment_id = payload_dict["attachment_id"]
        attachment_data = await ChatAttachmentsRepository.get_attachment_by_id(attachment_id=attachment_id)
        if not attachment_data or getattr(attachment_data, "status", None) == "deleted":
            raise ValueError(f"Attachment with ID {attachment_id} not found or already deleted.")

        s3_key = attachment_data.s3_key
        try:
            object_bytes = await ChatFileUpload.get_file_data_by_s3_key(s3_key=s3_key)
            s3_payload = json.loads(object_bytes.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise ValueError(f"Failed to decode JSON payload from S3: {e}")

        # Preserve important fields from original payload
        for field in ("session_id", "session_type", "auth_token"):
            if field in payload_dict:
                s3_payload[field] = payload_dict[field]

        # Cleanup S3 resources
        try:
            await ChatFileUpload.delete_file_by_s3_key(s3_key=s3_key)
        except Exception:  # noqa: BLE001
            AppLogger.log_error(f"Failed to delete S3 file {s3_key}")

        try:
            await ChatAttachmentsRepository.update_attachment_status(attachment_id, "deleted")
        except Exception:  # noqa: BLE001
            AppLogger.log_error(f"Failed to update status for attachment {attachment_id}")

        return s3_payload

    @staticmethod
    async def handle_session_data_caching(payload: QuerySolverInput) -> None:
        """Handle session data caching for the payload."""
        await CodeGenTasksCache.cleanup_session_data(payload.session_id)

        session_data_dict = {}
        if payload.query:
            session_data_dict["query"] = payload.query
            if payload.llm_model:
                session_data_dict["llm_model"] = payload.llm_model.value
            await CodeGenTasksCache.set_session_data(payload.session_id, session_data_dict)

    def is_s3_payload(self, payload_dict: Dict[str, Any]) -> bool:
        """
        Check if the payload is from S3 (has attachment_id).

        Args:
            payload_dict: Raw payload dictionary

        Returns:
            bool: True if this is an S3 payload, False otherwise
        """
        return payload_dict.get("type") == "PAYLOAD_ATTACHMENT" and payload_dict.get("attachment_id") is not None

    def is_resume_payload(self, payload: Union[QuerySolverInput, QuerySolverResumeInput]) -> bool:
        """
        Check if the payload is for resuming a stream.

        Args:
            payload: QuerySolverInput or QuerySolverResumeInput to check

        Returns:
            bool: True if this is a resume payload, False otherwise
        """
        return isinstance(payload, QuerySolverResumeInput)

    def is_normal_payload(self, payload: Union[QuerySolverInput, QuerySolverResumeInput]) -> bool:
        """
        Check if the payload is a normal query payload.

        Args:
            payload: QuerySolverInput or QuerySolverResumeInput to check

        Returns:
            bool: True if this is a normal payload, False otherwise
        """
        return isinstance(payload, QuerySolverInput) and not isinstance(payload, QuerySolverResumeInput)
