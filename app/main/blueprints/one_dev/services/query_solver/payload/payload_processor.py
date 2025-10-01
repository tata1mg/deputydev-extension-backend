import json
from typing import Any, Dict

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
        for field in ("session_id", "session_type", "auth_token", "user_team_id"):
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


    async def get_payload_from_raw_data(self, raw_data: Dict[str, Any]) -> QuerySolverInput | QuerySolverResumeInput:
        final_raw_payload = raw_data.copy()
        if raw_data.get("type") == "PAYLOAD_ATTACHMENT" and raw_data.get("attachment_id") is not None:
            # S3 attachment payload
            final_raw_payload = await self.process_s3_payload(raw_data)

        if final_raw_payload.get("resume_query_id") is not None:
            return QuerySolverResumeInput.model_validate(final_raw_payload)
        return QuerySolverInput.model_validate(final_raw_payload)
