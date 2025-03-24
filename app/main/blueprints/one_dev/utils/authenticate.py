import json
from functools import wraps
from typing import Any

from deputydev_core.utils.constants.auth import AuthStatus
from jwt import ExpiredSignatureError, InvalidTokenError
from torpedo import Request
from torpedo.exceptions import BadRequestException

from app.backend_common.models.dto.user_team_dto import UserTeamDTO
from app.backend_common.repository.user_teams.user_team_repository import (
    UserTeamRepository,
)
from app.backend_common.repository.users.user_repository import UserRepository
from app.backend_common.services.auth.session_encryption_service import (
    SessionEncryptionService,
)
from app.backend_common.services.auth.supabase.auth import SupabaseAuth
from app.main.blueprints.one_dev.services.auth.signup import SignUp
from app.main.blueprints.one_dev.utils.client.dataclasses.main import ClientData
from app.main.blueprints.one_dev.utils.dataclasses.main import AuthData


def authenticate(func: Any) -> Any:
    """
    Wrapper to authenticate the user.
    """

    @wraps(func)
    async def wrapper(_request: Request, client_data: ClientData, **kwargs: Any) -> Any:
        # Check if the session ID is present in the headers
        authorization_header = _request.headers.get("Authorization")
        # TODO: update below logic, this is very specific

        use_grace_period: bool = False
        enable_grace_period: bool = False
        try:
            payload = _request.custom_json() if _request.method == "POST" else _request.request_params()
            use_grace_period = payload.get("use_grace_period") or False
            enable_grace_period = payload.get("enable_grace_period") or False
        except Exception:
            pass
        if not authorization_header:
            raise Exception("Authorization header is missing")

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
                return {"status": AuthStatus.NOT_VERIFIED.value}
        except ExpiredSignatureError:
            # refresh the current session
            refresh_session_data = await SupabaseAuth.refresh_session(session_data)
            # add the session data to the kwargs
            kwargs["response_headers"] = {"new_session_data": refresh_session_data[0]}
        except InvalidTokenError:
            return {
                "status": AuthStatus.NOT_VERIFIED.value,
                "error_message": "Invalid token format.",
            }
        except Exception as _ex:
            return {
                "status": AuthStatus.NOT_VERIFIED.value,
                "error_message": str(_ex),
            }

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
        team_info = SignUp.get_team_info_from_email(email)
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

        # prepare the auth data
        auth_data = None
        if kwargs.get("response_headers") and kwargs["response_headers"]["new_session_data"]:
            auth_data = AuthData(
                user_team_id=user_team_id, refresh_session_data=kwargs["response_headers"]["new_session_data"]
            )
        else:
            auth_data = AuthData(user_team_id=user_team_id)

        return await func(_request, client_data=client_data, auth_data=auth_data, **kwargs)

    return wrapper
