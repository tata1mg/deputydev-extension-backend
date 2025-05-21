import asyncio
from typing import Any, Dict, List

from deputydev_core.utils.config_manager import ConfigManager

from app.backend_common.models.dto.message_thread_dto import (
    LLModels,
    ToolUseResponseContent,
    ToolUseResponseData,
)
from app.backend_common.services.llm.dataclasses.main import (
    NonStreamingParsedLLMCallResponse,
)
from app.backend_common.services.llm.handler import LLMHandler
from app.main.blueprints.one_dev.models.dto.job import JobDTO
from app.main.blueprints.one_dev.services.query_solver.dataclasses.main import (
    InlineEditInput,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.dataclasses.main import (
    PromptFeatures,
)
from app.main.blueprints.one_dev.services.query_solver.tools.focused_snippets_searcher import (
    FOCUSED_SNIPPETS_SEARCHER,
)
from app.main.blueprints.one_dev.services.query_solver.tools.file_editor import REPLACE_IN_FILE
from app.main.blueprints.one_dev.services.query_solver.tools.iterative_file_reader import ITERATIVE_FILE_READER
from app.main.blueprints.one_dev.services.query_solver.tools.related_code_searcher import (
    RELATED_CODE_SEARCHER,
)
from app.main.blueprints.one_dev.services.query_solver.tools.task_completed import TASK_COMPLETION
from app.main.blueprints.one_dev.services.repository.code_generation_job.main import (
    JobService,
)
from app.main.blueprints.one_dev.utils.client.dataclasses.main import ClientData
from app.main.blueprints.one_dev.utils.version import compare_version

from .prompts.factory import PromptFeatureFactory

MIN_SUPPORT_CLIENT_VERSION_FOR_NEW_FILE_EDITOR = "5.0.0"
MIN_SUPPORT_CLIENT_VERSION_FOR_TASK_COMPLETION = "5.0.0"
class InlineEditGenerator:
    def _get_response_from_parsed_llm_response(self, parsed_llm_response: List[Dict[str, Any]]) -> Dict[str, Any]:
        code_snippets: List[Dict[str, Any]] = []
        tool_use_request: Dict[str, Any] = {}
        for response in parsed_llm_response:
            if "code_snippets" in response:
                code_snippets.extend(response["code_snippets"])
            if "type" in response and response["type"] == "TOOL_USE_REQUEST":
                tool_use_request = response

        return {
            "code_snippets": code_snippets if code_snippets else None,
            "tool_use_request": tool_use_request if tool_use_request else None,
        }

    async def get_inline_edit_diff_suggestion(
        self, payload: InlineEditInput, client_data: ClientData
    ) -> Dict[str, Any]:
        llm_handler = LLMHandler(prompt_factory=PromptFeatureFactory, prompt_features=PromptFeatures)

        tools_to_use = [FOCUSED_SNIPPETS_SEARCHER, ITERATIVE_FILE_READER]
        if ConfigManager.configs["IS_RELATED_CODE_SEARCHER_ENABLED"]:
            tools_to_use.append(RELATED_CODE_SEARCHER)

        if compare_version(client_data.client_version, MIN_SUPPORT_CLIENT_VERSION_FOR_TASK_COMPLETION, ">="):
            if payload.llm_model and LLModels(payload.llm_model.value) == LLModels.GPT_4_POINT_1:
                tools_to_use.append(TASK_COMPLETION)
                payload.tool_choice = "required"
            
        if compare_version(client_data.client_version, MIN_SUPPORT_CLIENT_VERSION_FOR_NEW_FILE_EDITOR, ">="):
            tools_to_use.append(REPLACE_IN_FILE)

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
                tool_choice="required",
                stream=False,
            )

            if not isinstance(llm_response, NonStreamingParsedLLMCallResponse):
                raise ValueError("LLM response is not of type NonStreamingParsedLLMCallResponse")

            return self._get_response_from_parsed_llm_response(
                parsed_llm_response=llm_response.parsed_content,
            )

        if payload.query and payload.code_selection:
            llm_response = await llm_handler.start_llm_query(
                prompt_feature=PromptFeatures.INLINE_EDITOR,
                llm_model=LLModels(payload.llm_model.value),
                prompt_vars={
                    "query": payload.query,
                    "code_selection": payload.code_selection,
                    "deputy_dev_rules": payload.deputy_dev_rules,
                    "relevant_chunks": payload.relevant_chunks,
                },
                previous_responses=[],
                tools=tools_to_use,
                tool_choice="required",
                stream=False,
                session_id=payload.session_id,
            )

            if not isinstance(llm_response, NonStreamingParsedLLMCallResponse):
                raise ValueError("LLM response is not of type NonStreamingParsedLLMCallResponse")

            return self._get_response_from_parsed_llm_response(
                parsed_llm_response=llm_response.parsed_content,
            )

        raise ValueError("Either query and code selection or tool use response must be provided")

    async def start_job(self, payload: InlineEditInput, job_id: int, client_data: ClientData) -> int:
        try:
            data = await self.get_inline_edit_diff_suggestion(payload=payload, client_data=client_data)
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
                    "final_output": {"error": str(ex)},
                },
            )

    async def create_and_start_job(self, payload: InlineEditInput, client_data: ClientData) -> int:
        job = await JobService.db_create(
            JobDTO(
                type="INLINE_EDIT",
                session_id=str(payload.session_id),
                user_team_id=payload.auth_data.user_team_id,
                status="PENDING",
            )
        )
        asyncio.create_task(self.start_job(payload, job_id=job.id, client_data=client_data))
        return job.id
