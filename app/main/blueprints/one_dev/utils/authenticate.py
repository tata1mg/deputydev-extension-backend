from functools import wraps

from torpedo import CONFIG, Request
from torpedo.exceptions import BadRequestException

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
        status = await SupabaseAuth.verify_auth_token(access_token)
        if not status["valid"]:
            raise BadRequestException("Auth token not verified")

        # TODO: will change these values after implementing team fetch based on email of the user.
        team_id = 1
        user_id = 1

        # prepare the auth data
        auth_data = AuthData(
            team_id=team_id,
            user_id=user_id,
        )

        return await func(_request, auth_data=auth_data, **kwargs)

    return wrapper
