from enum import Enum


class AuthEndpoint(Enum):
    GET_AUTH_DATA = "/get-auth-data"
    GET_SESSION = "/get-session"
    VERIFY_AUTH_TOKEN = "/verify-auth-token"
    SIGN_UP = "/sign-up"
