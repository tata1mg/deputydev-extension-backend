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

rerank = Blueprint("rerank", "/rerank")


@rerank.route("/llm_based", methods=["POST"])
@validate_client_version
@authenticate
@ensure_session_id(session_type="CODE_GENERATION_V1")
async def reranker(_request: Request, client_data: ClientData, auth_data: AuthData, session_id: int, **kwargs):
    payload = _request.custom_json()
    payload = RerankingInput(**payload)
    response = await LLMBasedChunkReranker(session_id=session_id).rerank(
        query=payload.query, related_codebase_chunks=payload.relevant_chunks, focus_chunks=payload.focus_chunks or []
    )
    return send_response(response)
