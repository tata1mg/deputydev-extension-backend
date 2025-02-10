import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, TypeVar

from app.backend_common.services.llm.dataclasses.main import LLMMeta
from app.common.constants.constants import PromptFeatures
from app.main.blueprints.one_dev.models.dto.job import JobDTO
from app.main.blueprints.one_dev.models.dto.session_chat import SessionChatDTO
from app.main.blueprints.one_dev.services.code_generation.iterative_handlers.dataclass.main import (
    BaseCodeGenIterativeHandlerPayload,
    CodeGenIterativeHandlers,
)
from app.main.blueprints.one_dev.services.repository.code_generation_job.main import (
    JobService,
)
from app.main.blueprints.one_dev.services.repository.session_chat.main import (
    SessionChatService,
)

PayloadType = TypeVar("PayloadType", bound=BaseCodeGenIterativeHandlerPayload)


class BaseCodeGenIterativeHandler(ABC, Generic[PayloadType]):
    feature: CodeGenIterativeHandlers

    @classmethod
    async def _get_previous_responses(cls, payload: PayloadType) -> List[Dict[str, str]]:
        all_session_chats = await SessionChatService.db_get(
            filters={
                "session_id": payload.session_id,
                "prompt_type__in": [
                    prompt_feature.value
                    for prompt_feature in [
                        PromptFeatures.CODE_GENERATION,
                        PromptFeatures.DOCS_GENERATION,
                        PromptFeatures.TASK_PLANNER,
                        PromptFeatures.TEST_PLAN_GENERATION,
                        PromptFeatures.TEST_GENERATION,
                        PromptFeatures.ITERATIVE_CODE_CHAT,
                    ]
                ],
            }
        )
        sorted_session_chats: List[SessionChatDTO] = sorted(all_session_chats, key=lambda x: x.created_at)

        previous_responses: List[Dict[str, str]] = []
        for chat in sorted_session_chats:
            previous_responses.append({"role": "user", "content": chat.llm_prompt})
            previous_responses.append({"role": "assistant", "content": chat.llm_response})

        return previous_responses

    @classmethod
    @abstractmethod
    async def _feature_task(cls, payload: PayloadType, job_id: int, llm_meta: List[LLMMeta]) -> Dict[str, Any]:
        raise NotImplementedError("Method not implemented")

    @classmethod
    async def run_feature(cls, payload: PayloadType, job_id: int, llm_meta: List[LLMMeta]):
        try:
            result = await cls._feature_task(payload, job_id, llm_meta)
            await JobService.db_update(
                filters={"id": job_id},
                update_data={"status": "SUCCESS", "final_output": result},
            )
        except Exception as _ex:
            await JobService.db_update(
                filters={"id": job_id},
                update_data={"status": "FAILED", "final_output": {"error": str(_ex)}},
            )
            raise _ex

    @classmethod
    async def start_feature(cls, payload: PayloadType) -> Dict[str, int]:
        job = await JobService.db_create(
            code_generation_job=JobDTO(
                status="PENDING",
                session_id=payload.session_id,
                type=cls.feature.value,
                user_team_id=payload.auth_data.user_team_id,
            )
        )
        asyncio.create_task(cls.run_feature(payload, job.id, []))
        return {"job_id": job.id, "session_id": payload.session_id}
