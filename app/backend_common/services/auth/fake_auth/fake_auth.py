from typing import Dict

from deputydev_core.utils.config_manager import ConfigManager
from deputydev_core.utils.constants.auth import AuthStatus

from app.backend_common.services.auth.base_auth import BaseAuth
from app.backend_common.utils.dataclasses.main import AuthSessionData
from app.backend_common.utils.sanic_wrapper import Request


class FakeAuth(BaseAuth):
    async def get_auth_session(self, headers: Dict[str, str]) -> AuthSessionData:
        return AuthSessionData(
            status=AuthStatus.AUTHENTICATED,
            user_email=ConfigManager.configs["FAKE_AUTH"]["USER_EMAIL"],
            user_name=ConfigManager.configs["FAKE_AUTH"]["USER_NAME"],
            encrypted_session_data=ConfigManager.configs["FAKE_AUTH"]["ENCRYPTED_SESSION_DATA"],
        )

    async def extract_and_verify_token(self, request: Request) -> AuthSessionData:
        return AuthSessionData(
            status=AuthStatus.VERIFIED,
            user_email=ConfigManager.configs["FAKE_AUTH"]["USER_EMAIL"],
            user_name=ConfigManager.configs["FAKE_AUTH"]["USER_NAME"],
            encrypted_session_data=ConfigManager.configs["FAKE_AUTH"]["ENCRYPTED_SESSION_DATA"],
        )
