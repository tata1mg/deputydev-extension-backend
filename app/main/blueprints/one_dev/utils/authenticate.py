from functools import wraps

from torpedo import CONFIG, Request
from torpedo.exceptions import BadRequestException

from app.backend_common.repository.user_teams.user_team_service import UserTeamService
from app.backend_common.repository.users.user_service import UserService
from app.backend_common.services.supabase.auth import SupabaseAuth
from app.common.services.authentication.jwt import JWTHandler
from app.main.blueprints.one_dev.constants.constants import TATA_1MG, TRAYA
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
        email = session_data.get("email")
        if not email:
            raise BadRequestException("Email not found in session data")

        # Fetch the user ID based on the email
        user = await UserService.db_get(filters={"email": email}, fetch_one=True)
        user_id = user.id

        # If the user ID is not found, raise an error
        if not user_id:
            raise BadRequestException("User not found")

        # Team id will be on the basis of email domain
        domain = email.split("@")[1]
        if domain == TATA_1MG["domain"]:
            team_id = TATA_1MG["team_id"]
        elif domain == TRAYA["domain"]:
            team_id = TRAYA["team_id"]
        else:
            team_id = None

        # If the team ID is not found, raise an error
        if not team_id:
            raise BadRequestException("Team not found")

        # Fetch the user team ID based on the user ID and team ID
        user_team = await UserTeamService.db_get(filters={"user_id": user_id, "team_id": team_id}, fetch_one=True)
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
