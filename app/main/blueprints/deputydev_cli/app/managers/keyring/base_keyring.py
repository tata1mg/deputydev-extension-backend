from typing import Union
import keyring
from app.common.utils.config_manager import ConfigManager

class BaseKeyRing:
    app_name = ConfigManager.configs["APP_NAME"]

    @classmethod
    def store_auth_token(cls, token: str):
        """Stores the auth_token securely using keyring.

        Args:
            token (str): The authentication token to store.
        """
        keyring.set_password(cls.app_name, cls.key_name, token)

    @classmethod
    def load_auth_token(cls) -> Union[str, None]:
        """Loads the auth_token securely using keyring.

        Returns:
            Union[str, None]: The stored authentication token if found, otherwise None.
        """
        return keyring.get_password(cls.app_name, cls.key_name)