import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, TypeVar

from app.backend_common.services.llm.providers.dataclass.main import LLMMeta
from app.main.blueprints.one_dev.models.dto.job import JobDTO
from app.main.blueprints.one_dev.services.code_generation.features.dataclass.main import (
    BaseCodeGenFeaturePayload,
    CodeGenFeature,
)
from app.main.blueprints.one_dev.services.repository.code_generation_job.main import (
    JobService,
)

PayloadType = TypeVar("PayloadType", bound=BaseCodeGenFeaturePayload)


class BaseCodeGenFeature(ABC, Generic[PayloadType]):
    feature: CodeGenFeature

    @classmethod
    @abstractmethod
    async def _feature_task(cls, payload: PayloadType, job_id: int, llm_meta: List[LLMMeta]) -> Dict[str, Any]:
        raise NotImplementedError("Method not implemented")

    @classmethod
    async def run_feature(cls, payload: PayloadType, job_id: int):
        try:
            result = await cls._feature_task(payload, job_id, [])
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
                team_id=payload.auth_data.team_id,
                user_id=payload.auth_data.user_id,
            )
        )
        asyncio.create_task(cls.run_feature(payload, job.id))
        return {"job_id": job.id, "session_id": payload.session_id}
