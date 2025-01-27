from abc import ABC, abstractmethod
from typing import Union


class BaseKeyRing(ABC):
    def __init__(self, app_name: str):
        self.app_name = app_name

    @abstractmethod
    def store_auth_token(self, token: str):
        """Stores the auth_token securely using keyring.

        This method must be implemented in a child class.
        """
        raise NotImplementedError("The store method must be implemented in the child class.")

    @abstractmethod
    def load_auth_token(self) -> Union[str, None]:
        """Loads the auth_token securely using keyring.

        This method must be implemented in a child class.
        """
        raise NotImplementedError("The load method must be implemented in the child class.")
