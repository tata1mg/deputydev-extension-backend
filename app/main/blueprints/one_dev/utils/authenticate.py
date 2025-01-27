import json
from functools import wraps

from torpedo import Request
from torpedo.exceptions import BadRequestException

from app.backend_common.repository.user_teams.user_team_repository import (
    UserTeamRepository,
)
from app.backend_common.repository.users.user_repository import UserRepository
from app.backend_common.services.auth.session_encryption_service import (
    SessionEncryptionService,
)
from app.backend_common.services.auth.supabase.auth import SupabaseAuth
from app.main.blueprints.one_dev.services.auth.signup import SignUp
from app.main.blueprints.one_dev.utils.dataclasses.main import AuthData


def authenticate(func):
    """
    Wrapper to authenticate the user using the JWT token.
    """

    @wraps(func)
    async def wrapper(_request: Request, **kwargs):
        # Check if the session ID is present in the headers
        authorization_header = _request.headers.get("Authorization")
        if not authorization_header:
            raise Exception("Authorization header is missing")

        # decode the JWT token and get the supabase access token
        jwt = authorization_header.split(" ")[1]
        # first decrypt the token using session encryption service
        session_data_string = SessionEncryptionService.decrypt(jwt)
        # convert back to json object
        session_data = json.loads(session_data_string)
        # extract supabase access token
        access_token = session_data.get("access_token")
        token_data = await SupabaseAuth.verify_auth_token(access_token)
        if not token_data["valid"]:
            raise BadRequestException("Auth token not verified")

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
        user_team = await UserTeamRepository.db_get(filters={"user_id": user_id, "team_id": team_id}, fetch_one=True)
        user_team_id = user_team.id

        # If the user team ID is not found, raise an error
        if not user_team_id:
            raise BadRequestException("User team not found")

        # prepare the auth data
        auth_data = AuthData(
            user_team_id=user_team_id,
        )

        return await func(_request, auth_data=auth_data, **kwargs)

    return wrapper
