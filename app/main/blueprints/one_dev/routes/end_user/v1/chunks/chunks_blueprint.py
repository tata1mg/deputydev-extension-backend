from typing import Any

from sanic import Blueprint
from sanic.response import JSONResponse
from torpedo import Request, send_response
from torpedo.response import ResponseDict

from app.backend_common.services.chunking.rerankers.handler.llm_based.reranker import (
    LLMBasedChunkReranker,
)
from app.backend_common.utils.authenticate import authenticate
from app.backend_common.utils.dataclasses.main import AuthData, ClientData
from app.main.blueprints.one_dev.models.dto.reranking_input import RerankingInput
from app.main.blueprints.one_dev.utils.client.client_validator import (
    validate_client_version,
)
from app.main.blueprints.one_dev.utils.session import ensure_session_id

chunks_v1_bp = Blueprint("chunks_v1_bp", url_prefix="/chunks")


@chunks_v1_bp.route("/rerank-via-llm", methods=["POST"])
@validate_client_version
@authenticate
@ensure_session_id(auto_create=True)
async def reranker(
    _request: Request, client_data: ClientData, auth_data: AuthData, session_id: int, **kwargs: Any
) -> ResponseDict | JSONResponse:
    payload = _request.custom_json()
    payload = RerankingInput(**payload)
    reranked_chunks = await LLMBasedChunkReranker(session_id=session_id).rerank(
        query=payload.query, related_codebase_chunks=payload.relevant_chunks, focus_chunks=payload.focus_chunks or []
    )
    return send_response(
        {"reranked_denotations": [chunk.denotation for chunk in reranked_chunks], "session_id": session_id}
    )
