from __future__ import annotations

import typing as t

import jwt
from torpedo import CONFIG


class JWTService:
    """Service for encoding and decoding JSON Web Tokens (JWT).

    Attributes:
        SIGNING_KEY (str): The key used to sign the JWTs.
        ALGORITHM (str): The algorithm used for signing the JWTs.
    """

    SIGNING_KEY = CONFIG.config["WEBHOOK_JWT_SIGNING_KEY"]
    ALGORITHM = "HS256"

    @classmethod
    def encode(cls, payload: dict[str, t.Any]) -> str:
        """Encode a payload into a JSON Web Token (JWT).

        Args:
            payload (dict[str, t.Any]): The payload data to encode in the JWT.

        Returns:
            str: The encoded JWT.
        """
        encoded = jwt.encode(
            payload=payload,
            key=cls.SIGNING_KEY,
            algorithm=cls.ALGORITHM,
        )
        return encoded

    @classmethod
    def decode(cls, token: str) -> dict[str, t.Any]:
        """Decode a JSON Web Token (JWT) back into its payload.

        Args:
            token (str): The JWT to decode.

        Returns:
            dict[str, t.Any]: The decoded payload.
        """
        decoded_payload = jwt.decode(
            jwt=token,
            key=cls.SIGNING_KEY,
            algorithms=cls.ALGORITHM,
        )
        return decoded_payload
