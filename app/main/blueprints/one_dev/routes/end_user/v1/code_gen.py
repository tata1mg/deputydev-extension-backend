from sanic import Blueprint
from torpedo import CONFIG, Request, send_response

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
from app.main.blueprints.one_dev.services.code_generation.iterative_handlers.plan_code_generation.dataclasses.main import (
    PlanCodeGenerationInput,
)
from app.main.blueprints.one_dev.services.code_generation.iterative_handlers.plan_code_generation.main import (
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
from app.main.blueprints.one_dev.utils.dataclasses.main import AuthData
from app.main.blueprints.one_dev.utils.session import ensure_session_id

code_gen = Blueprint("code_gen", "/")

config = CONFIG.config


@code_gen.route("/generate-code", methods=["POST"])
@ensure_session_id
@authenticate
async def generate_code(_request: Request, auth_data: AuthData, **kwargs):
    payload = _request.custom_json()
    response = await CodeGenerationHandler.start_feature(
        payload=CodeGenerationInput(**payload, session_id=_request.headers.get("X-Session-Id"), auth_data=auth_data)
    )
    return send_response(response)


@code_gen.route("/generate-docs", methods=["POST"])
@ensure_session_id
@authenticate
async def generate_docs(_request: Request, auth_data: AuthData, **kwargs):
    payload = _request.custom_json()
    response = await DocsGenerationHandler.start_feature(
        payload=CodeDocsGenerationInput(**payload, session_id=_request.headers.get("X-Session-Id"), auth_data=auth_data)
    )
    return send_response(response)


@code_gen.route("/generate-test-cases", methods=["POST"])
@ensure_session_id
@authenticate
async def generate_test_case(_request: Request, auth_data: AuthData, **kwargs):
    payload = _request.custom_json()
    response = await TestCaseGenerationHandler.start_feature(
        payload=TestCaseGenerationInput(**payload, session_id=_request.headers.get("X-Session-Id"), auth_data=auth_data)
    )
    return send_response(response)


@code_gen.route("/generate-code-plan", methods=["POST"])
@ensure_session_id
@authenticate
async def generate_code_plan(_request: Request, auth_data: AuthData, **kwargs):
    payload = _request.custom_json()
    response = await CodePlanHandler.start_feature(
        payload=CodePlanGenerationInput(**payload, session_id=_request.headers.get("X-Session-Id"), auth_data=auth_data)
    )
    return send_response(response)


@code_gen.route("/generate-diff", methods=["POST"])
@ensure_session_id
@authenticate
async def generate_code_diff(_request: Request, auth_data: AuthData, **kwargs):
    payload = _request.custom_json()
    response = await DiffCreationHandler.start_feature(
        payload=DiffCreationInput(session_id=_request.headers.get("X-Session-Id"), **payload, auth_data=auth_data)
    )
    return send_response(response)


@code_gen.route("/iterative-chat", methods=["POST"])
@ensure_session_id
@authenticate
async def iterative_chat(_request: Request, auth_data: AuthData, **kwargs):
    payload = _request.custom_json()
    response = await IterativeChatHandler.start_feature(
        payload=IterativeChatInput(**payload, session_id=_request.headers.get("X-Session-Id"), auth_data=auth_data)
    )
    return send_response(response)


@code_gen.route("/plan-code-generation", methods=["POST"])
@ensure_session_id
@authenticate
async def plan_code_generation(_request: Request, auth_data: AuthData, **kwargs):
    response = await PlanCodeGenerationHandler.start_feature(
        payload=PlanCodeGenerationInput(session_id=_request.headers.get("X-Session-Id"), auth_data=auth_data)
    )
    return send_response(response)


@code_gen.route("/get-job-status", methods=["GET"])
@ensure_session_id
@authenticate
async def get_job_status(_request: Request, auth_data: AuthData, **kwargs):
    payload = {key: var for key, var in _request.query_args}
    job = await JobService.db_get(
        filters={"id": int(payload.get("job_id")), "session_id": _request.headers.get("X-Session-Id")}, fetch_one=True
    )
    if not job:
        return send_response({"status": "JOB_NOT_FOUND"})
    response = {
        "status": job.status,
        "response": job.final_output,
    }
    return send_response(response)


@code_gen.route("/create-embedding", methods=["POST"])
@authenticate
async def get_embeddings(_request: Request, auth_data: AuthData, **kwargs):
    payload = _request.custom_json()
    response = await OneDevEmbeddingManager.create_embeddings(
        payload=OneDevEmbeddingPayload(**payload, auth_data=auth_data)
    )
    return send_response(response)
