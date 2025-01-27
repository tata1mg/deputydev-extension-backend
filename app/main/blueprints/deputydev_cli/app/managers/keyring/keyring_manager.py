from typing import Union

import keyring

from app.main.blueprints.deputydev_cli.app.managers.keyring.base_keyring_manager import (
    BaseKeyRing,
)


class AuthTokenKeyRing(BaseKeyRing):
    def __init__(self, app_name: str):
        """Initializes the AuthTokenKeyRing with the application name."""
        super().__init__(app_name)

    def store_auth_token(self, token: str):
        """Stores the auth_token securely using keyring.

        Args:
            token (str): The authentication token to store.
        """
        keyring.set_password(self.app_name, "auth_token", token)

    def load_auth_token(self) -> Union[str, None]:
        """Loads the auth_token securely using keyring.

        Returns:
            Union[str, None]: The stored authentication token if found, otherwise None.
        """
        return keyring.get_password(self.app_name, "auth_token")
