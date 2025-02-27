from sanic import Blueprint

from app.backend_common.services.chunking.reranker.handler.llm_based import LLMBasedChunkReranker
from app.main.blueprints.one_dev.utils.authenticate import authenticate
from torpedo import Request, send_response
from app.main.blueprints.one_dev.utils.dataclasses.main import AuthData
from pydantic import BaseModel
from deputydev_core.services.chunking.chunk_info import ChunkInfo
from typing import Optional

rerank = Blueprint("rerank", "/")


class RerankingInput(BaseModel):
    query: str
    relevant_chunks: list[ChunkInfo]
    focus_chunks: Optional[list[ChunkInfo]]
    is_llm_reranking_enabled: Optional[bool] = False


# @rerank.route("/llm_based", methods=["POST"])
# @authenticate
# async def reranker(_request: Request, auth_data: AuthData, **kwargs):
@rerank.route("/llm_reranking", methods=["POST"])
async def reranker(_request: Request):
    payload = _request.custom_json()
    payload = RerankingInput(**payload)
    response = await LLMBasedChunkReranker().rerank(
        query=payload.query, related_codebase_chunks=payload.relevant_chunks, focus_chunks=payload.focus_chunks
    )
    return send_response(response)
