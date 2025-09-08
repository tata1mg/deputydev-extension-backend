import json
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Dict, Tuple

from deputydev_core.utils.constants.auth import AuthStatus
from deputydev_core.utils.context_value import ContextValue
from sanic.server.websockets.impl import WebsocketImplProtocol

from app.backend_common.constants.onboarding import SubscriptionStatus
from app.backend_common.models.dto.user_team_dto import UserTeamDTO
from app.backend_common.repository.subscriptions.repository import SubscriptionsRepository
from app.backend_common.repository.user_teams.user_team_repository import (
    UserTeamRepository,
)
from app.backend_common.repository.users.user_repository import UserRepository
from app.backend_common.services.auth.auth_factory import AuthFactory
from app.backend_common.services.auth.signup import SignUp
from app.backend_common.utils.dataclasses.main import AuthData, AuthSessionData, ClientData
from app.backend_common.utils.sanic_wrapper import Request
from app.backend_common.utils.sanic_wrapper.exceptions import BadRequestException


async def get_auth_data(request: Request) -> Tuple[AuthData, Dict[str, Any]]:  # noqa: C901
    """
    Get the auth data from the request
    """
    response_headers = {}
    auth_provider = AuthFactory.get_auth_provider()
    verification_result: AuthSessionData = await auth_provider.extract_and_verify_token(request)

    if verification_result.status == AuthStatus.NOT_VERIFIED:
        raise BadRequestException(verification_result.error_message or AuthStatus.NOT_VERIFIED.value)

    if verification_result.status == AuthStatus.EXPIRED:
        response_headers = {"new_session_data": verification_result.encrypted_session_data}

    # Extract the email from the user response
    email = verification_result.user_email
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
