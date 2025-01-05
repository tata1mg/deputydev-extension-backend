from typing import List

from app.backend_common.services.llm.handler import LLMHandler
from app.common.constants.constants import LLModels, PromptFeatures
from app.common.services.chunking.chunk_info import ChunkInfo
from app.common.services.chunking.reranker.base_chunk_reranker import BaseChunkReranker
from app.common.services.chunking.utils.snippet_renderer import render_snippet_array
from app.common.services.prompt.factory import PromptFeatureFactory


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
        llm_response = await LLMHandler(prompt=prompt).get_llm_response_data(previous_responses=[])
        return llm_response.parsed_llm_data["filtered_chunks"]
