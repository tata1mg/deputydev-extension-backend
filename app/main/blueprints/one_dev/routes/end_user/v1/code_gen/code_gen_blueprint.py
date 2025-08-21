from typing import Any

from sanic import Blueprint
from app.backend_common.utils.sanic_wrapper import Request, send_response

from app.main.blueprints.one_dev.services.code_generation.features.code_generator.dataclasses.main import (
    CodeGenerationInput,
)
from app.main.blueprints.one_dev.services.code_generation.features.code_generator.main import (
    CodeGenerationHandler,
)
from app.main.blueprints.one_dev.services.code_generation.features.docs_generator.dataclasses.main import (
    CodeDocsGenerationInput,
)
from app.main.blueprints.one_dev.services.code_generation.features.docs_generator.main import (
    DocsGenerationHandler,
)
from app.main.blueprints.one_dev.services.code_generation.features.plan_generator.dataclasses.main import (
    CodePlanGenerationInput,
)
from app.main.blueprints.one_dev.services.code_generation.features.plan_generator.main import (
    CodePlanHandler,
)
from app.main.blueprints.one_dev.services.code_generation.features.test_case_generator.dataclasses.main import (
    TestCaseGenerationInput,
)
from app.main.blueprints.one_dev.services.code_generation.features.test_case_generator.main import (
    TestCaseGenerationHandler,
)
from app.main.blueprints.one_dev.services.code_generation.feedback.dataclasses.main import (
    CodeGenerationFeedbackInput,
)
from app.main.blueprints.one_dev.services.code_generation.feedback.main import (
    FeedbackService,
)
from app.main.blueprints.one_dev.services.code_generation.iterative_handlers.diff_creation.dataclasses.main import (
    DiffCreationInput,
)
from app.main.blueprints.one_dev.services.code_generation.iterative_handlers.diff_creation.main import (
    DiffCreationHandler,
)
from app.main.blueprints.one_dev.services.code_generation.iterative_handlers.iterative_chat.dataclasses.main import (
    IterativeChatInput,
)
from app.main.blueprints.one_dev.services.code_generation.iterative_handlers.iterative_chat.main import (
    IterativeChatHandler,
)
from app.main.blueprints.one_dev.services.code_generation.iterative_handlers.plan_to_code.dataclasses.main import (
    PlanCodeGenerationInput,
)
from app.main.blueprints.one_dev.services.code_generation.iterative_handlers.plan_to_code.main import (
    PlanCodeGenerationHandler,
)
from app.main.blueprints.one_dev.services.embedding.dataclasses.main import (
    OneDevEmbeddingPayload,
)
from app.main.blueprints.one_dev.services.embedding.manager import (
    OneDevEmbeddingManager,
)
from app.main.blueprints.one_dev.services.repository.code_generation_job.main import (
    JobService,
)
from app.main.blueprints.one_dev.utils.authenticate import authenticate
from app.main.blueprints.one_dev.utils.client.client_validator import (
    validate_client_version,
)
from app.main.blueprints.one_dev.utils.client.dataclasses.main import ClientData
from app.main.blueprints.one_dev.utils.dataclasses.main import AuthData
from app.main.blueprints.one_dev.utils.session import ensure_session_id

code_gen_v1_bp = Blueprint("code_gen_v1_bp", url_prefix="/code-gen")


@code_gen_v1_bp.route("/generate-code", methods=["POST"])
@validate_client_version
@authenticate
@ensure_session_id(auto_create=True)
async def generate_code(
    _request: Request, client_data: ClientData, auth_data: AuthData, session_id: int, **kwargs: Any
):
    payload = _request.custom_json()
    response = await CodeGenerationHandler.start_feature(
        payload=CodeGenerationInput(**payload, session_id=session_id, auth_data=auth_data)
    )
    return send_response(response, headers=kwargs.get("response_headers"))


@code_gen_v1_bp.route("/generate-docs", methods=["POST"])
@validate_client_version
@authenticate
@ensure_session_id(auto_create=True)
async def generate_docs(
    _request: Request, client_data: ClientData, auth_data: AuthData, session_id: int, **kwargs: Any
):
    payload = _request.custom_json()
    response = await DocsGenerationHandler.start_feature(
        payload=CodeDocsGenerationInput(**payload, session_id=session_id, auth_data=auth_data)
    )
    return send_response(response, headers=kwargs.get("response_headers"))


@code_gen_v1_bp.route("/generate-test-cases", methods=["POST"])
@validate_client_version
@authenticate
@ensure_session_id(auto_create=True)
async def generate_test_case(
    _request: Request, client_data: ClientData, auth_data: AuthData, session_id: int, **kwargs: Any
):
    payload = _request.custom_json()
    response = await TestCaseGenerationHandler.start_feature(
        payload=TestCaseGenerationInput(**payload, session_id=session_id, auth_data=auth_data)
    )
    return send_response(response, headers=kwargs.get("response_headers"))


@code_gen_v1_bp.route("/generate-code-plan", methods=["POST"])
@validate_client_version
@authenticate
@ensure_session_id(auto_create=True)
async def generate_code_plan(
    _request: Request, client_data: ClientData, auth_data: AuthData, session_id: int, **kwargs: Any
):
    payload = _request.custom_json()
    response = await CodePlanHandler.start_feature(
        payload=CodePlanGenerationInput(**payload, session_id=session_id, auth_data=auth_data)
    )
    return send_response(response, headers=kwargs.get("response_headers"))


@code_gen_v1_bp.route("/generate-diff", methods=["POST"])
@validate_client_version
@authenticate
@ensure_session_id(auto_create=False)
async def generate_code_diff(
    _request: Request, client_data: ClientData, auth_data: AuthData, session_id: int, **kwargs: Any
):
    payload = _request.custom_json()
    response = await DiffCreationHandler.start_feature(
        payload=DiffCreationInput(session_id=session_id, **payload, auth_data=auth_data)
    )
    return send_response(response, headers=kwargs.get("response_headers"))


@code_gen_v1_bp.route("/iterative-chat", methods=["POST"])
@validate_client_version
@authenticate
@ensure_session_id(auto_create=False)
async def iterative_chat(
    _request: Request, client_data: ClientData, auth_data: AuthData, session_id: int, **kwargs: Any
):
    payload = _request.custom_json()
    response = await IterativeChatHandler.start_feature(
        payload=IterativeChatInput(**payload, session_id=session_id, auth_data=auth_data)
    )
    return send_response(response, headers=kwargs.get("response_headers"))


@code_gen_v1_bp.route("/plan-code-generation", methods=["POST"])
@validate_client_version
@authenticate
@ensure_session_id(auto_create=False)
async def plan_to_code(_request: Request, client_data: ClientData, auth_data: AuthData, session_id: int, **kwargs: Any):
    response = await PlanCodeGenerationHandler.start_feature(
        payload=PlanCodeGenerationInput(session_id=session_id, auth_data=auth_data)
    )
    return send_response(response, headers=kwargs.get("response_headers"))


@code_gen_v1_bp.route("/get-job-status", methods=["GET"])
@validate_client_version
@authenticate
async def get_job_status(_request: Request, client_data: ClientData, auth_data: AuthData, **kwargs: Any):
    payload = {key: var for key, var in _request.query_args}
    job = await JobService.db_get(filters={"id": int(payload.get("job_id"))}, fetch_one=True)
    if not job:
        return send_response({"status": "JOB_NOT_FOUND"})
    response = {
        "status": job.status,
        "response": job.final_output,
    }
    return send_response(response, headers=kwargs.get("response_headers"))


@code_gen_v1_bp.route("/create-embedding", methods=["POST"])
@validate_client_version
# @authenticate
async def get_embeddings(_request: Request, client_data: ClientData, **kwargs: Any):
    payload = _request.custom_json()
    response = await OneDevEmbeddingManager.create_embeddings(payload=OneDevEmbeddingPayload(**payload))
    return send_response(response, headers=kwargs.get("response_headers"))


@code_gen_v1_bp.route("/record-feedback", methods=["POST"])
@validate_client_version
@authenticate
async def record_feedback(_request: Request, client_data: ClientData, auth_data: AuthData, **kwargs: Any):
    payload = _request.custom_json()
    response = await FeedbackService.record_feedback(payload=CodeGenerationFeedbackInput(**payload))
    return send_response(response, headers=kwargs.get("response_headers"))
