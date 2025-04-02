import asyncio
from typing import Any, Dict

from app.backend_common.models.dto.message_thread_dto import LLModels, ToolUseResponseContent, ToolUseResponseData
from app.backend_common.services.llm.handler import LLMHandler
from app.main.blueprints.one_dev.models.dto.job import JobDTO
from app.main.blueprints.one_dev.services.query_solver.dataclasses.main import (
    InlineEditInput,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.dataclasses.main import (
    PromptFeatures,
)
from app.main.blueprints.one_dev.services.query_solver.tools.related_code_searcher import RELATED_CODE_SEARCHER
from app.main.blueprints.one_dev.services.repository.code_generation_job.main import (
    JobService,
)

from .prompts.factory import PromptFeatureFactory


class InlineEditGenerator:
    async def get_inline_edit_diff_suggestion(self, payload: InlineEditInput) -> Dict[str, Any]:
        if not (payload.query and payload.code_selection) and not payload.tool_use_response:
            raise ValueError("Either query and code selection or tool use response must be provided")

        llm_handler = LLMHandler(prompt_factory=PromptFeatureFactory, prompt_features=PromptFeatures)
        tools_to_use = [RELATED_CODE_SEARCHER]

        if payload.tool_use_response:
            llm_response = await llm_handler.submit_tool_use_response(
                session_id=payload.session_id,
                tool_use_response=ToolUseResponseData(
                    content=ToolUseResponseContent(
                        tool_name=payload.tool_use_response.tool_name,
                        tool_use_id=payload.tool_use_response.tool_use_id,
                        response=payload.tool_use_response.response,
                    )
                ),
                tools=tools_to_use,
                stream=False,
            )
            return llm_response.parsed_content[0]

        if payload.query and payload.code_selection:
            llm_response = await llm_handler.start_llm_query(
                prompt_feature=PromptFeatures.INLINE_EDITOR,
                llm_model=LLModels.CLAUDE_3_POINT_5_SONNET,
                prompt_vars={
                    "query": payload.query,
                    "code_selection": payload.code_selection,
                    "deputy_dev_rules": payload.deputy_dev_rules,
                },
                previous_responses=[],
                tools=tools_to_use,
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
