from sanic import Blueprint

from app.backend_common.services.chunking.reranker.handler.llm_based import LLMBasedChunkReranker
from app.main.blueprints.one_dev.utils.authenticate import authenticate
from torpedo import Request, send_response
from app.main.blueprints.one_dev.utils.dataclasses.main import AuthData
from app.main.blueprints.one_dev.models.dto.reranking_input import RerankingInput

rerank = Blueprint("rerank", "/rerank")


@rerank.route("/llm_based", methods=["POST"])
# @authenticate
# async def reranker(_request: Request, auth_data: AuthData, **kwargs):
async def reranker(_request: Request):
    payload = _request.custom_json()
    payload = RerankingInput(**payload)
    response = await LLMBasedChunkReranker().rerank(
        query=payload.query, related_codebase_chunks=payload.relevant_chunks, focus_chunks=payload.focus_chunks
    )
    return send_response(response)