import asyncio
from typing import Any, Dict

from app.backend_common.models.dto.message_thread_dto import LLModels
from app.backend_common.services.llm.handler import LLMHandler
from app.main.blueprints.one_dev.models.dto.job import JobDTO
from app.main.blueprints.one_dev.services.query_solver.dataclasses.main import (
    InlineEditInput,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.dataclasses.main import (
    PromptFeatures,
)
from app.main.blueprints.one_dev.services.repository.code_generation_job.main import (
    JobService,
)

from .prompts.factory import PromptFeatureFactory


class InlineEditGenerator:
    async def get_inline_edit_diff_suggestion(self, payload: InlineEditInput) -> Dict[str, Any]:
        llm_handler = LLMHandler(prompt_factory=PromptFeatureFactory, prompt_features=PromptFeatures)
        llm_response = await llm_handler.start_llm_query(
            prompt_feature=PromptFeatures.INLINE_EDITOR,
            llm_model=LLModels.CLAUDE_3_POINT_5_SONNET,
            prompt_vars={
                "query": payload.query,
                "relevant_chunks": payload.relevant_chunks,
                "code_selection": payload.code_selection,
            },
            previous_responses=[],
            tools=[],
            stream=False,
            session_id=payload.session_id,
        )
        return llm_response.parsed_content[0]

    async def start_job(self, payload: InlineEditInput, job_id: int) -> int:
        try:
            data = await self.get_inline_edit_diff_suggestion(payload)
            await JobService.db_update(
                {
                    "id": job_id,
                },
                {
                    "status": "COMPLETED",
                    "final_output": data,
                },
            )
        except Exception as ex:
            await JobService.db_update(
                {
                    "id": job_id,
                },
                {
                    "status": "FAILED",
                    "final_output": str(ex),
                },
            )

    async def create_and_start_job(self, payload: InlineEditInput) -> int:
        job = await JobService.db_create(
            JobDTO(
                type="INLINE_EDIT",
                session_id=str(payload.session_id),
                user_team_id=payload.auth_data.user_team_id,
                status="PENDING",
            )
        )
        asyncio.create_task(self.start_job(payload, job_id=job.id))
        return job.id

    async def get_inline_diff_result(self, headers: Dict[str, Any]) -> Dict[str, Any]:
        try:
            job_id = headers["job_id"]
            if not job_id:
                raise ValueError("job_id is required")
            inline_diff_result = await JobService.db_get(filters={"id": job_id}, fetch_one=True)
            if inline_diff_result.status != "COMPLETED":
                return {
                    "status": "PENDING",
                }
            return {
                "status": "COMPLETED",
                "result": inline_diff_result.final_output,
            }
        except Exception as ex:
            return {
                "status": "FAILED",
                "error": str(ex),
            }
