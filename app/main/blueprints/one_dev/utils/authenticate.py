from functools import wraps

from torpedo import CONFIG, Request

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

        # decode the token
        token = authorization_header.split(" ")[1]
        token_data = JWTHandler(signing_key=CONFIG.config["JWT_SECRET_KEY"]).verify_token(token)
        headers = _request.headers

        # get user name and user email
        user_name = headers.get("X-User-Name")
        user_email = headers.get("X-User-Email")

        # prepare the auth data
        auth_data = AuthData(
            team_id=token_data["team_id"],
            advocacy_id=token_data["advocacy_id"],
            user_email=user_email,
            user_name=user_name,
        )

        return await func(_request, auth_data=auth_data, **kwargs)

    return wrapper
