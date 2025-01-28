from app.main.blueprints.deputydev_cli.app.constants.cli import KeyringConstants
from app.main.blueprints.deputydev_cli.app.managers.keyring.base_keyring import BaseKeyRing

class AuthTokenKeyRing(BaseKeyRing):
    """
    A class to manage the authentication token using the keyring.

    Inherits from BaseKeyRing and defines the key_name for storing
    and retrieving the authentication token.

    Attributes:
        key_name (str): The name of the key used to store the authentication token.
    """
    key_name = KeyringConstants.AUTH_TOKEN.value