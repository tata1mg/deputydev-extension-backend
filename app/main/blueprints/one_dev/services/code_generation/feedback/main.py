from typing import Any, Dict
from app.main.blueprints.one_dev.models.dto.job_feedback import JobFeedbackDTO
from app.main.blueprints.one_dev.services.code_generation.feedback.dataclasses.main import CodeGenerationFeedbackInput
from app.main.blueprints.one_dev.services.repository.job_feedback.main import JobFeedbackService


class FeedbackService:
    @classmethod
    async def record_feedback(cls, payload: CodeGenerationFeedbackInput) -> Dict[str, Any]:
        # check if job feedback already exists
        job_feedback = await JobFeedbackService.db_get(
            filters={"job_id": payload.job_id}, fetch_one=True
        )

        if job_feedback:
            await JobFeedbackService.db_update(
                filters={"job_id": payload.job_id},
                update_data={"feedback": payload.feedback.value},
            )
        else:
            await JobFeedbackService.db_create(
                JobFeedbackDTO(job_id=payload.job_id, feedback=payload.feedback)
            )

        return {"message": "Feedback recorded successfully"}