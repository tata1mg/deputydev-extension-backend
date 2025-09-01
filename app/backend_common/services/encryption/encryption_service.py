from __future__ import annotations

import base64
import os

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.backend_common.utils.sanic_wrapper import CONFIG


class EncryptionService:
    """
    AES-256 encryption and decryption utility class.

    This class provides methods to encrypt and decrypt strings using the
    AES-256 algorithm with a password-derived key.

    Attributes:
        password (bytes): The encryption password used to derive the key.
        salt (bytes): A cryptographic salt used during key derivation.
        key (bytes): The derived AES-256 key.
    """

    SALT_LENGTH = 16
    IV_LENGTH = 16
    KEY_LENGTH = 32
    ITERATIONS = 100000

    PASSWORD_STR: str = CONFIG.config["ENCRYPTION_PASSWORD"]
    PASSWORD: bytes = PASSWORD_STR.encode()

    @classmethod
    def encrypt(cls, plaintext: str) -> str:
        """
        Encrypts the provided plaintext using AES-256-CBC and returns Base64-encoded ciphertext.

        Args:
            password (str): The password used for key derivation.
            plaintext (str): The plaintext string to encrypt.

        Returns:
            str: Base64-encoded encrypted data (salt + IV + ciphertext).
        """
        padded_data = cls.__pad(plaintext=plaintext)

        # Generate random salt
        salt = os.urandom(cls.SALT_LENGTH)

        # derive AES-256 key from password and salt
        key = cls.__derive_key(salt=salt)

        # Generate a random 16-byte initialization vector (IV)
        iv = os.urandom(cls.IV_LENGTH)

        cipher = cls._get_cipher(key=key, iv=iv)
        encryptor = cipher.encryptor()

        # Encrypt the padded data
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()

        encoded_data = cls.__encode(salt, iv, ciphertext)

        return encoded_data

    @classmethod
    def decrypt(cls, encrypted_data: str) -> str:
        """
        Decrypts the Base64-encoded ciphertext back into plaintext.

        Args:
            password (str): The password used for key derivation.
            encrypted_data (str): Base64-encoded encrypted data (salt + IV + ciphertext).

        Returns:
            str: The original plaintext.
        """

        salt, iv, ciphertext = cls.__decode(encrypted_data)

        # Derive the AES key using the same salt
        key = cls.__derive_key(salt=salt)

        cipher = cls._get_cipher(key=key, iv=iv)
        decryptor = cipher.decryptor()

        # Decrypt the ciphertext
        padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()

        plaintext = cls.__unpad(padded_plaintext=padded_plaintext)

        return plaintext.decode()

    @classmethod
    def _get_cipher(cls, key: bytes, iv: bytes) -> Cipher:
        """
        Creates an AES cipher object with CBC mode using the provided key and IV.

        Args:
            key (bytes): The AES key.
            iv (bytes): The initialization vector.

        Returns:
            Cipher: The AES cipher object.
        """
        return Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())

    @classmethod
    def __derive_key(cls, salt: bytes) -> bytes:
        """
        Derives a 256-bit AES key from the password and salt using PBKDF2.

        Args:
            password (bytes): The password in byte form.
            salt (bytes): The cryptographic salt.

        Returns:
            bytes: A 32-byte (256-bit) AES key.
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),  # Use SHA256 for key derivation
            length=cls.KEY_LENGTH,  # Generate a 32-byte key for AES-256
            salt=salt,
            iterations=cls.ITERATIONS,
            backend=default_backend(),
        )
        return kdf.derive(cls.PASSWORD)

    @classmethod
    def __unpad(cls, padded_plaintext: bytes) -> bytes:
        """
        Unpads the plaintext to remove padding added during encryption.

        Args:
            padded_plaintext (bytes): The padded plaintext.

        Returns:
            bytes: The unpadded plaintext.
        """
        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
        plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()
        return plaintext

    @classmethod
    def __pad(cls, plaintext: str) -> bytes:
        """
        Pads the plaintext to match AES block size (16 bytes).

        Args:
            plaintext (str): The plaintext string to pad.

        Returns:
            bytes: The padded plaintext.
        """
        padder = padding.PKCS7(algorithms.AES.block_size).padder()
        padded_data = padder.update(plaintext.encode()) + padder.finalize()
        return padded_data

    @classmethod
    def __encode(cls, salt: bytes, iv: bytes, ciphertext: bytes) -> str:
        """
        Encodes the salt, IV, and ciphertext into a Base64-encoded string.

        Args:
            salt (bytes): The cryptographic salt.
            iv (bytes): The initialization vector.
            ciphertext (bytes): The encrypted ciphertext.

        Returns:
            str: The Base64-encoded encrypted data.
        """
        encrypted_data = salt + iv + ciphertext
        return base64.b64encode(encrypted_data).decode("utf-8")

    @classmethod
    def __decode(cls, encoded_data: str) -> tuple[bytes, bytes, bytes]:
        """
        Decodes the Base64-encoded encrypted data back to binary format and extracts the salt, IV, and ciphertext.

        Args:
            encoded_data (str): The Base64-encoded encrypted data.

        Returns:
            tuple[bytes, bytes, bytes]: The salt, IV, and ciphertext.
        """
        decoded_cipher_bytes = base64.b64decode(encoded_data)

        salt = decoded_cipher_bytes[: cls.SALT_LENGTH]  # First 16 bytes for salt
        iv = decoded_cipher_bytes[cls.SALT_LENGTH : cls.SALT_LENGTH + cls.IV_LENGTH]  # Next 16 bytes for IV
        ciphertext = decoded_cipher_bytes[cls.SALT_LENGTH + cls.IV_LENGTH :]  # Remaining bytes for ciphertext

        return salt, iv, ciphertext
