from app.backend_common.services.encryption.encryption_service import EncryptionService
from app.backend_common.utils.sanic_wrapper import CONFIG


class SessionEncryptionService(EncryptionService):
    """
    A service for handling session encryption using the functionalities provided
    by the EncryptionService class.

    Attributes:
        PASSWORD_STR (str): The encryption password retrieved from the configuration.
        PASSWORD (bytes): The encoded version of the encryption password.
    """

    PASSWORD_STR: str = CONFIG.config["SESSION_ENCRYPTION_PASSWORD"]
    PASSWORD: bytes = PASSWORD_STR.encode()
