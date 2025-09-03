from typing import Any

from deputydev_core.utils.app_logger import AppLogger
from sanic import Blueprint
from sanic.response import JSONResponse

from app.backend_common.utils.sanic_wrapper import CONFIG, Request, send_response
from app.backend_common.utils.sanic_wrapper.types import ResponseDict
from app.backend_common.utils.authenticate import authenticate
from app.backend_common.utils.dataclasses.main import AuthData
from app.main.blueprints.deputy_dev.services.code_review.ide_review.dataclass.main import GetRepoIdRequest
from app.main.blueprints.deputy_dev.services.code_review.ide_review.pre_processors.ide_review_pre_processor import (
    IdeReviewPreProcessor,
)
from app.main.blueprints.one_dev.utils.client.client_validator import (
    validate_client_version,
)

repos = Blueprint("repos", "/repos")

config = CONFIG.config


@repos.route("/get-repo-id", methods=["GET"])
@validate_client_version
@authenticate
async def get_repo_id(request: Request, auth_data: AuthData, **kwargs: Any) -> JSONResponse | ResponseDict:
    try:
        query_params = request.request_params()
        data = GetRepoIdRequest(**query_params)
        processor = IdeReviewPreProcessor()
        repo_dto = await processor.get_repo_id(data, auth_data.user_team_id)
        return send_response({"repo_id": repo_dto.id})
    except Exception as e:  # noqa: BLE001
        AppLogger.log_error(f"Error getting repo id: {e}")
        return send_response({"status": "ERROR", "message": str(e)})
