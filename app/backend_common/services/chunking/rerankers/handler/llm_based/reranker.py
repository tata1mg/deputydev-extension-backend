import asyncio
import time
from typing import List, Optional

from deputydev_core.llm_handler.dataclasses.main import (
    NonStreamingParsedLLMCallResponse,
)
from deputydev_core.llm_handler.models.dto.message_thread_dto import (
    LLModels,
    MessageCallChainCategory,
)
from deputydev_core.services.chunking.chunk_info import ChunkInfo
from deputydev_core.services.chunking.utils.snippet_renderer import render_snippet_array
from deputydev_core.services.reranker.base_chunk_reranker import BaseChunkReranker
from deputydev_core.utils.app_logger import AppLogger

from app.backend_common.services.llm.llm_service_manager import LLMServiceManager

from .prompts.dataclasses.main import PromptFeatures
from .prompts.factory import PromptFeatureFactory


class LLMBasedChunkReranker(BaseChunkReranker):
    def __init__(self, session_id: int) -> None:
        super().__init__()
        self.session_id = session_id

    @classmethod
    def get_chunks_from_denotation(cls, chunks: List[ChunkInfo], denotations: List[str]) -> List[ChunkInfo]:
        result: List[ChunkInfo] = []
        for chunk in chunks:
            if chunk.denotation in denotations:
                result.append(chunk)
        return result

    async def rerank(
        self,
        query: str,
        relevant_chunks: List[ChunkInfo],
    ) -> List[ChunkInfo]:
        llm_handler = LLMServiceManager().create_llm_handler(
            prompt_factory=PromptFeatureFactory,
            prompt_features=PromptFeatures,
        )

        start_time = time.perf_counter()  # Record the start time
        max_retries = 2
        response: Optional[NonStreamingParsedLLMCallResponse] = None
        for attempt in range(max_retries + 1):
            try:
                llm_response = await llm_handler.start_llm_query(
                    session_id=self.session_id,
                    prompt_feature=PromptFeatures.CHUNK_RE_RANKING,
                    llm_model=LLModels.GPT_4_POINT_1_MINI,
                    prompt_vars={
                        "query": query,
                        "relevant_chunks": render_snippet_array(relevant_chunks),
                    },
                    call_chain_category=MessageCallChainCategory.SYSTEM_CHAIN,
                )
                if llm_response:
                    if not isinstance(llm_response, NonStreamingParsedLLMCallResponse):
                        raise ValueError("Expected NonStreamingParsedLLMCallResponse")
                    response = llm_response
                    break
            except Exception as e:  # noqa: BLE001
                AppLogger.log_warn(f"LLM reranking call Attempt {attempt + 1} failed: {e}")
                await asyncio.sleep(1)  # Optional: add a delay before retrying
        # Calculate the duration
        duration = time.perf_counter() - start_time
        AppLogger.log_info(f"Time taken for llm reranking: {duration:.2f} seconds")
        if response and response.parsed_content and isinstance(response.parsed_content, list):
            try:
                chunks_source: List[str] = response.parsed_content[0]["chunks_source"]
            except (IndexError, KeyError, TypeError) as e:
                AppLogger.log_error(f"Malformed parsed_content in LLM response: {response.parsed_content}, error: {e}")
                return []
            return self.get_chunks_from_denotation(relevant_chunks, chunks_source)
        else:
            AppLogger.log_warn("Empty or invalid LLM response: No reranked chunks found")
            return []
