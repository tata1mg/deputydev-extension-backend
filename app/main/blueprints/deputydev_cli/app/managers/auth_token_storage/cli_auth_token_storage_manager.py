from app.main.blueprints.deputydev_cli.app.constants.cli import AuthTokenConstants
from app.main.blueprints.deputydev_cli.app.managers.auth_token_storage.base_auth_token_storage_manager import (
    AuthTokenStorageBase,
)


class CLIAuthTokenStorageManager(AuthTokenStorageBase):
    """
    A class to manage the authentication token using a persistent storage mechanism.

    Inherits from AuthTokenStorageBase and defines the key_name for storing
    and retrieving the authentication token.

    Attributes:
        key_name (str): The name of the key used to store the authentication token,
                        derived from the AuthTokenConstants.
    """

    key_name = AuthTokenConstants.CLI_AUTH_TOKEN.value
