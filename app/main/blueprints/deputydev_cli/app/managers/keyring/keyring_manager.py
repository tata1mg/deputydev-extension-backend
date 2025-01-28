from typing import Union

from app.main.blueprints.deputydev_cli.app.constants.cli import KeyringConstants
from app.main.blueprints.deputydev_cli.app.managers.keyring.base_keyring_manager import (
    BaseKeyRing,
)


class AuthTokenKeyRing(BaseKeyRing):
    def __init__(self):
        """Initializes the AuthTokenKeyRing with the application name."""
        super().__init__()

    @classmethod
    def store_auth_token(cls, token: str):
        """Stores the auth_token securely using keyring."""
        super().store_auth_token(KeyringConstants.AUTH_TOKEN.value, token)

    @classmethod
    def load_auth_token(cls) -> Union[str, None]:
        """Loads the auth_token securely using keyring."""
        return super().load_auth_token(KeyringConstants.AUTH_TOKEN.value)
