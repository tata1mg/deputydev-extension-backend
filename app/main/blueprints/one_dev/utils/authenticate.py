from functools import wraps

from torpedo import CONFIG, Request
from torpedo.exceptions import BadRequestException

from app.backend_common.repository.user_teams.user_team_service import UserTeamService
from app.backend_common.repository.users.user_service import UserService
from app.backend_common.services.supabase.auth import SupabaseAuth
from app.common.services.authentication.jwt import JWTHandler
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
        session_data = JWTHandler(signing_key=CONFIG.config["JWT_SECRET_KEY"]).verify_token(jwt)
        access_token = session_data.get("access_token")
        token_data = await SupabaseAuth.verify_auth_token(access_token)
        if not token_data["valid"]:
            raise BadRequestException("Auth token not verified")

        # Extract the email from the user response
        email = token_data["user_response"]

        # Fetch the user ID based on the email
        user = await UserService.db_get(filters={"email": email}, fetch_one=True)
        user_id = user.id

        # If the user ID is not found, raise an error
        if not user_id:
            raise BadRequestException("User not found")

        # Fetch the team ID based on the user ID
        user_team = await UserTeamService.db_get(filters={"user_id": user_id}, fetch_one=True)
        team_id = user_team.team_id

        # If the team ID is not found, raise an error
        if not team_id:
            raise BadRequestException("Team not found")

        # prepare the auth data
        auth_data = AuthData(
            team_id=team_id,
            user_id=user_id,
        )

        return await func(_request, auth_data=auth_data, **kwargs)

    return wrapper
