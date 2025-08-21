from typing import Any, Dict

from app.backend_common.models.dao.postgres.extension_sessions import ExtensionSession
from app.backend_common.repository.db import DB
from app.backend_common.repository.message_threads.repository import (
    MessageThreadsRepository,
)
from app.main.blueprints.one_dev.models.dto.job_feedback import JobFeedbackDTO
from app.main.blueprints.one_dev.services.feedback.dataclasses.main import CodeGenerationFeedbackInput
from app.main.blueprints.one_dev.services.repository.extension_feedbacks.repository import (
    ExtensionFeedbacksRepository,
)
from app.main.blueprints.one_dev.services.repository.job_feedback.main import (
    JobFeedbackService,
)


class FeedbackService:
    @classmethod
    async def record_feedback(cls, payload: CodeGenerationFeedbackInput) -> Dict[str, Any]:
        # check if job feedback already exists
        job_feedback = await JobFeedbackService.db_get(filters={"job_id": payload.job_id}, fetch_one=True)

        if job_feedback:
            await JobFeedbackService.db_update(
                filters={"job_id": payload.job_id},
                update_data={"feedback": payload.feedback.value},
            )
        else:
            await JobFeedbackService.db_create(JobFeedbackDTO(job_id=payload.job_id, feedback=payload.feedback))

        return {"message": "Feedback recorded successfully"}

    @classmethod
    async def record_extension_feedback(
        cls, query_id: int, feedback: str, session_id: int, user_team_id: int
    ) -> Dict[str, Any]:
        message_thread = await MessageThreadsRepository.get_message_thread_by_id(message_thread_id=query_id)
        if not message_thread or message_thread.session_id != session_id:
            raise ValueError("Invalid query_id/session_id provided")

        extension_session = await DB.by_filters(
            model_name=ExtensionSession,
            where_clause={"session_id": session_id, "user_team_id": user_team_id},
            fetch_one=True,
        )
        if not extension_session:
            raise ValueError("Session id is invalid or you don't have permission to record feedback")

        await ExtensionFeedbacksRepository.submit_feedback(query_id=query_id, feedback=feedback)
        return {"message": "Extension feedback recorded successfully"}
