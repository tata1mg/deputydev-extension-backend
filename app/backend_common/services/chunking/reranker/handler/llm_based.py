import asyncio
import time
from typing import List

from app.backend_common.services.llm.handler import LLMHandler
from app.backend_common.constants.constants import LLModels
from app.common.constants.constants import PromptFeatures
from deputydev_core.services.chunking.chunk_info import ChunkInfo
from deputydev_core.services.reranker.base_chunk_reranker import BaseChunkReranker
from deputydev_core.services.chunking.utils.snippet_renderer import render_snippet_array
from app.common.services.prompt.factory import PromptFeatureFactory
from deputydev_core.utils.app_logger import AppLogger


class LLMBasedChunkReranker(BaseChunkReranker):
    async def rerank(
        self,
        focus_chunks: List[ChunkInfo],
        related_codebase_chunks: List[ChunkInfo],
        query: str,
    ) -> List[ChunkInfo]:
        prompt = PromptFeatureFactory.get_prompt(
            prompt_feature=PromptFeatures.RE_RANKING,
            model_name=LLModels.CLAUDE_3_POINT_5_SONNET,
            init_params={
                "query": query,
                "focus_chunks": render_snippet_array(focus_chunks),
                "related_chunk": render_snippet_array(related_codebase_chunks),
            },
        )

        start_time = time.perf_counter()  # Record the start time
        max_retries = 2
        response = None
        for attempt in range(max_retries + 1):
            try:
                response = await LLMHandler(prompt=prompt).get_llm_response_data(previous_responses=[])
                if response:
                    break
            except Exception as e:
                AppLogger.log_warn(f"LLM reranking call Attempt {attempt + 1} failed: {e}")
                await asyncio.sleep(1)  # Optional: add a delay before retrying

        # Calculate the duration
        duration = time.perf_counter() - start_time
        AppLogger.log_info(f"Time taken for llm reranking: {duration:.2f} seconds")
        if response:
            filtered_chunks = response.parsed_llm_data["filtered_chunks"]
            return filtered_chunks
