from typing import Union

import keyring

from app.common.utils.config_manager import ConfigManager


class BaseKeyRing:
    def __init__(self, app_name: str = None):
        self.app_name = app_name if app_name else ConfigManager.configs["APP_NAME"]

    @classmethod
    def store_auth_token(cls, key: str, token: str):
        """Stores the auth_token securely using keyring.

        Args:
            key (str): The key under which to store the token.
            token (str): The authentication token to store.
        """
        keyring.set_password(cls().app_name, key, token)

    @classmethod
    def load_auth_token(cls, key: str) -> Union[str, None]:
        """Loads the auth_token securely using keyring.

        Args:
            key (str): The key under which the token is stored.

        Returns:
            Union[str, None]: The stored authentication token if found, otherwise None.
        """
        return keyring.get_password(cls().app_name, key)
