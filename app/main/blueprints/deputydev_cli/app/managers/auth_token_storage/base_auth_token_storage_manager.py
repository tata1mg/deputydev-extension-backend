import json
import os
from typing import Union

from app.main.blueprints.deputydev_cli.app.constants.cli import (
    LocalDirectories,
    LocalFiles,
)


class AuthTokenStorageBase:
    """
    A base class for managing authentication tokens using persistent storage.

    This class provides methods to store and load authentication tokens
    in a JSON file located in a hidden directory in the user's home directory.

    Attributes:
        token_file (str): The path to the JSON file used for storing the token.

    Methods:
        store_auth_token(token): Stores the provided authentication token in the JSON file.
        load_auth_token(): Loads the authentication token from the JSON file, returning None if not found.
    """

    token_dir = os.path.join(os.path.expanduser("~"), LocalDirectories.LOCAL_ROOT_DIRECTORY.value)
    token_file = os.path.join(token_dir, LocalFiles.CLI_AUTH_TOKEN_FILE.value)

    @classmethod
    def ensure_token_directory(cls):
        os.makedirs(cls.token_dir, exist_ok=True)

    @classmethod
    def store_auth_token(cls, token: str):
        cls.ensure_token_directory()
        with open(cls.token_file, "w") as f:
            json.dump({cls.key_name: token}, f)

    @classmethod
    def load_auth_token(cls) -> Union[str, None]:
        if os.path.exists(cls.token_file):
            with open(cls.token_file, "r") as f:
                data = json.load(f)
                return data.get(cls.key_name)
        return None
