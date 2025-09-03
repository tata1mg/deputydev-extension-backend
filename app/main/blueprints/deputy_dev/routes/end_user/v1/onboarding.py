from sanic import Blueprint, Request, response
from sanic.response import JSONResponse
from sanic_ext import validate

from app.backend_common.exception.exception import OnboardingError
from app.backend_common.utils.sanic_wrapper.response import get_error_body_response
from app.main.blueprints.deputy_dev.models.request import (
    OnboardingRequest,
    SignUpRequest,
)
from app.main.blueprints.deputy_dev.services.workspace.onboarding_manager import (
    OnboardingManager,
)

onboarding_bp = Blueprint("onboarding", url_prefix="/onboard")


# ---------------------------------------------------------------------------- #
#                                    Sign Up                                   #
# ---------------------------------------------------------------------------- #


@onboarding_bp.post("/signup")
@validate(json=SignUpRequest)
async def signup(req: Request, body: SignUpRequest) -> JSONResponse:
    await OnboardingManager.signup(payload=body)
    return response.json({"user": "created"})


# ---------------------------------------------------------------------------- #
#                            Onboarding SCM Account                            #
# ---------------------------------------------------------------------------- #


@onboarding_bp.post("/integration")
@validate(json=OnboardingRequest)
async def onboard_org(request: Request, body: OnboardingRequest) -> JSONResponse:
    try:
        await OnboardingManager.onboard(payload=body)
    except OnboardingError as exc:
        return get_error_body_response(error=str(exc), status_code=500)

    return response.json({"onboarded": body.integration_client})
