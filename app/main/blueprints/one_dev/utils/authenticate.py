import json
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Dict, Tuple

from deputydev_core.utils.constants.auth import AuthStatus
from deputydev_core.utils.context_value import ContextValue
from jwt import ExpiredSignatureError, InvalidTokenError
from sanic.server.websockets.impl import WebsocketImplProtocol

from app.backend_common.constants.onboarding import SubscriptionStatus
from app.backend_common.models.dto.user_team_dto import UserTeamDTO
from app.backend_common.repository.subscriptions.repository import SubscriptionsRepository
from app.backend_common.repository.user_teams.user_team_repository import (
    UserTeamRepository,
)
from app.backend_common.repository.users.user_repository import UserRepository
from app.backend_common.services.auth.session_encryption_service import (
    SessionEncryptionService,
)
from app.backend_common.services.auth.supabase.auth import SupabaseAuth
from app.backend_common.utils.sanic_wrapper import CONFIG, Request
from app.backend_common.utils.sanic_wrapper.exceptions import BadRequestException
from app.main.blueprints.one_dev.services.auth.signup import SignUp
from app.main.blueprints.one_dev.utils.client.dataclasses.main import ClientData
from app.main.blueprints.one_dev.utils.dataclasses.main import AuthData
from app.main.blueprints.one_dev.utils.session import get_stored_session


async def get_auth_data(request: Request) -> Tuple[AuthData, Dict[str, Any]]:  # noqa: C901
    """
    Get the auth data from the request
    """
    # TODO: SLIGHTLY FUCKED UP. DUPLICATE OF verify_auth_token
    # Check if the session ID is present in the headers
    response_headers = {}
    authorization_header: str = request.headers.get("Authorization")
    use_grace_period: bool = False
    enable_grace_period: bool = False
    bypass_token = CONFIG.config.get("REVIEW_AUTH_TOKEN")
    if authorization_header and bypass_token and authorization_header.split(" ")[1].strip() == bypass_token:
        session_id = request.headers.get("X-Session-ID")
        session = await get_stored_session(session_id)
        if not session:
            raise BadRequestException("Invalid or missing session for bypass token")
        auth_data = AuthData(user_team_id=session.user_team_id)
        response_headers["_bypass_review_auth"] = True
        return auth_data, response_headers

    try:
        payload: Dict[str, Any] = request.custom_json() if request.method == "POST" else request.request_params()
        use_grace_period = payload.get("use_grace_period") or False
        enable_grace_period = payload.get("enable_grace_period") or False
    except Exception:  # noqa: BLE001
        pass
    if not authorization_header:
        raise Exception("Authorization header is missing")

    session_data: Dict[str, Any] = {}
    # decode encrypted session data and get the supabase access token
    encrypted_session_data = authorization_header.split(" ")[1].strip()
    try:
        # first decrypt the token using session encryption service
        session_data_string = SessionEncryptionService.decrypt(encrypted_session_data)
        # convert back to json object
        session_data = json.loads(session_data_string)
        # extract supabase access token
        access_token = session_data.get("access_token")
        token_data = await SupabaseAuth.verify_auth_token(
            access_token.strip(), use_grace_period=use_grace_period, enable_grace_period=enable_grace_period
        )
        if not token_data["valid"]:
            raise BadRequestException(AuthStatus.NOT_VERIFIED.value)
    except ExpiredSignatureError:
        # refresh the current session
        refresh_session_data = await SupabaseAuth.refresh_session(session_data)
        # add the session data to the kwargs
        response_headers = {"new_session_data": refresh_session_data[0]}
    except InvalidTokenError:
        raise BadRequestException("Invalid token")
    except Exception:  # noqa: BLE001
        raise BadRequestException(AuthStatus.NOT_VERIFIED.value)

    # Extract the email from the user response
    email = session_data.get("email")
    if not email:
        raise BadRequestException("Email not found in session data")

    # Fetch the user ID based on the email
    user = await UserRepository.db_get(filters={"email": email}, fetch_one=True)
    user_id = user.id

    # If the user ID is not found, raise an error
    if not user_id:
        raise BadRequestException("User not found")

    # Get the team ID based on the email domain
    team_info = await SignUp.get_team_info_from_email(email)
    team_id = team_info.get("team_id")

    # If the team ID is not found, raise an error
    if not team_id:
        raise BadRequestException("Team not found")

    # Fetch the user team ID based on the user ID and team ID
    user_team: UserTeamDTO = await UserTeamRepository.db_get(
        filters={"user_id": user_id, "team_id": team_id}, fetch_one=True
    )
    user_team_id = user_team.id

    # If the user team ID is not found, raise an error
    if not user_team_id:
        raise BadRequestException("User team not found")

    # Check subscription
    subscription = await SubscriptionsRepository.get_by_user_team_id(user_team_id)
    if not subscription:
        raise BadRequestException("Subscription not found")

    # Check subscription expiry
    if subscription.end_date is not None and (
        subscription.end_date < datetime.now(timezone.utc)
        or SubscriptionStatus(subscription.current_status) != SubscriptionStatus.ACTIVE
    ):
        raise BadRequestException("Subscription expired")

    # prepare the auth data
    auth_data = None
    if response_headers and response_headers["new_session_data"]:
        auth_data = AuthData(user_team_id=user_team_id, session_refresh_token=response_headers["new_session_data"])
    else:
        auth_data = AuthData(user_team_id=user_team_id)

    return auth_data, response_headers


def authenticate(func: Any) -> Any:
    """
    Wrapper to authenticate the user.
    """

    @wraps(func)
    async def wrapper(request: Request, *args: Any, **kwargs: Any) -> Any:
        try:
            # Get the auth data
            client_data: ClientData = kwargs.get("client_data")
            auth_data, response_headers = await get_auth_data(request)
            kwargs["response_headers"] = response_headers
            ContextValue.set("response_headers", response_headers)
        except Exception as ex:  # noqa: BLE001
            if args and isinstance(args[0], WebsocketImplProtocol):
                error_data = {
                    "type": "STREAM_ERROR",
                    "message": "Unable to authenticate user",
                    "status": "NOT_VERIFIED",
                }
                await args[0].send(json.dumps(error_data))
            raise BadRequestException(str(ex), sentry_raise=False)
        kwargs = {
            **kwargs,
            "auth_data": auth_data,
            "client_data": client_data,
        }
        return await func(request, *args, **kwargs)

    return wrapper
