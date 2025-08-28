from typing import Any, Dict

from deputydev_core.utils.config_manager import ConfigManager
from deputydev_core.utils.constants.auth import AuthStatus

from app.backend_common.services.auth.base_auth import BaseAuth


class FakeAuth(BaseAuth):
    async def extract_and_verify_token(self, headers: Dict[str, str], payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "status": AuthStatus.VERIFIED.value,
            "user_email": ConfigManager.configs["FAKE_AUTH"]["USER_EMAIL"],
            "user_name": ConfigManager.configs["FAKE_AUTH"]["USER_NAME"],
            "encrypted_session_data": ConfigManager.configs["FAKE_AUTH"]["ENCRYPTED_SESSION_DATA"],
        }
