from typing import Any

from sanic import Blueprint
from torpedo import Request, send_response

from app.backend_common.services.chunking.rerankers.handler.llm_based.reranker import (
    LLMBasedChunkReranker,
)
from app.main.blueprints.one_dev.models.dto.reranking_input import RerankingInput
from app.main.blueprints.one_dev.utils.authenticate import authenticate
from app.main.blueprints.one_dev.utils.client.client_validator import (
    validate_client_version,
)
from app.main.blueprints.one_dev.utils.client.dataclasses.main import ClientData
from app.main.blueprints.one_dev.utils.dataclasses.main import AuthData
from app.main.blueprints.one_dev.utils.session import ensure_session_id

chunks_v1_bp = Blueprint("chunks_v1_bp", url_prefix="/chunks")


@chunks_v1_bp.route("a", methods=["POST"])
@validate_client_version
@authenticate
@ensure_session_id(auto_create=True)
async def reranker(_request: Request, **kwargs: Any):
    payload = _request.custom_json()
    session_id = _request.headers.get("X-Session-ID")
    payload = RerankingInput(**payload)
    reranked_chunks = await LLMBasedChunkReranker(session_id=session_id).rerank(
        query=payload.query, related_codebase_chunks=payload.relevant_chunks, focus_chunks=payload.focus_chunks or []
    )
    return send_response(
        {"reranked_denotations": [chunk.denotation for chunk in reranked_chunks], "session_id": session_id}
    )
