from torpedo import CONFIG

from app.backend_common.services.encryption.encryption_service import EncryptionService


class UserExtensionRepoEncryptionService(EncryptionService):
    """
    A service for handling session encryption using the functionalities provided
    by the EncryptionService class.

    Attributes:
        PASSWORD_STR (str): The encryption password retrieved from the configuration.
        PASSWORD (bytes): The encoded version of the encryption password.
    """

    PASSWORD_STR: str = CONFIG.config["EXTENSION_REPOS_ENCRYPTION_PASSWORD"]
    PASSWORD: bytes = PASSWORD_STR.encode()

    @classmethod
    def generate_repo_hash(cls, repo_name: str, repo_path: str) -> str:
        unique_string = f"{repo_name}:{repo_path}"
        return cls.encrypt(unique_string)
