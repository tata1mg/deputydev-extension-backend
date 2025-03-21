import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, TypeVar

from deputydev_core.services.chunking.chunk_info import ChunkInfo
from deputydev_core.utils.config_manager import ConfigManager

from app.backend_common.services.chunking.rerankers.handler.llm_based.reranker import (
    LLMBasedChunkReranker,
)
from app.backend_common.services.llm.dataclasses.main import LLMMeta
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
                user_team_id=payload.auth_data.user_team_id,
            )
        )
        asyncio.create_task(cls.run_feature(payload, job.id))
        return {"job_id": job.id, "session_id": payload.session_id}

    @classmethod
    async def rerank(
        cls,
        query: str,
        relevant_chunks: List[ChunkInfo],
        focus_chunks: List[ChunkInfo],
        is_llm_reranking_enabled: bool,
        sesison_id: int,
    ) -> List[ChunkInfo]:
        filtered_and_ranked_chunks = None
        if is_llm_reranking_enabled:
            filtered_and_ranked_chunks = await LLMBasedChunkReranker(session_id=sesison_id).rerank(
                query=query, related_codebase_chunks=relevant_chunks, focus_chunks=focus_chunks
            )
            return filtered_and_ranked_chunks
        elif not is_llm_reranking_enabled or not filtered_and_ranked_chunks:
            filtered_and_ranked_chunks = cls.get_default_chunks(focus_chunks, relevant_chunks)
        return filtered_and_ranked_chunks

    @classmethod
    def get_default_chunks(
        cls, focus_chunks: List[ChunkInfo], related_codebase_chunks: List[ChunkInfo]
    ) -> List[ChunkInfo]:
        max_default_chunks_to_return = ConfigManager.config["CHUNKING"]["DEFAULT_MAX_CHUNKS_CODE_GENERATION"]
        chunks = focus_chunks + related_codebase_chunks
        chunks.sort(key=lambda chunk: chunk.search_score, reverse=True)
        return chunks[:max_default_chunks_to_return]
