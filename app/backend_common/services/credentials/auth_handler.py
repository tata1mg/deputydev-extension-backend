from __future__ import annotations

from contextvars import ContextVar
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Tuple

from git.util import Actor
from tortoise.exceptions import DoesNotExist

from app.backend_common.constants.constants import TokenableType, TokenType
from app.backend_common.exception.exception import CredentialsError
from app.backend_common.models.dao.postgres.tokens import Tokens
from app.backend_common.services.encryption.encryption_service import EncryptionService

_TOKEN_STORE: ContextVar[Dict[str, Any]] = ContextVar("token_store", default={})
"""Task-local token store."""


class AuthHandler:
    """Token retrieval, storage and access management."""

    __integration__: str = "base"
    __tokenable_type__: str = "integration"

    _encryption_service: EncryptionService = EncryptionService

    def __init__(self, tokenable_id: int):
        self.tokenable_id = tokenable_id

    # --------------------------- implement in subclass -------------------------- #

    async def _authorise(self, *args, **kwargs):
        raise NotImplementedError

    async def _refresh(self, *args, **kwargs):
        raise NotImplementedError

    # -------------------------------- public apis ------------------------------- #

    async def access_token(self) -> str:
        """
        Retrieve the access token, refreshing it if necessary.

        Returns:
            str: The access token.

        Raises:
            CredentialsError: If tokens are not found in the datastore.
        """
        # -- read from task ctx --
        if ctx := _TOKEN_STORE.get():
            if client_ctx := ctx.get(self.__integration__):
                tkn = client_ctx.get("access_token")
                expiry = client_ctx.get("expiry")

                if not self._has_expired(expiry=expiry):
                    # happy flow!
                    return tkn
        # -- read from datastore --
        tkn, expiry, refresh_tkn = await self.load()

        if not self._has_expired(expiry=expiry):
            # store to ctx
            self.save_to_ctx(tkn, expiry)
            return tkn

        # -- refresh --
        tkn, expiry, refresh_tkn = await self.refresh(refresh_tkn=refresh_tkn)
        await self.dump(tkn, expiry, refresh_tkn)

        return tkn

    @classmethod
    async def get_workspace_access_token(cls, dd_workspace_id: int) -> str:
        token_row = await Tokens.get(
            type=TokenType.WORKSPACE_ACCESS.value,
            tokenable_type=TokenableType.WORKSPACE.value,
            tokenable_id=dd_workspace_id,
        )

        token = token_row.token
        token = cls._encryption_service.decrypt(token)
        return token

    async def authorise(self, auth_code: str) -> Tuple[str, datetime, str]:
        """
        Get access and refresh tokens from the authorisation server.

        Args:
            auth_code (str): The authorisation code.

        Returns:
            Tuple[str, datetime, str]: The access token, its expiry time, and the refresh token.
        """
        # authorise
        tkn, expiry, refresh_tkn = await self._authorise(auth_code)

        # update ctx
        self.save_to_ctx(tkn, expiry)

        return tkn, expiry, refresh_tkn

    async def refresh(self, refresh_tkn: str) -> Tuple[str, datetime, str]:
        """
        Use the refresh token to get a fresh access token.

        Args:
            refresh_tkn (str): The refresh token.

        Returns:
            Tuple[str, datetime, str]: The new access token, its expiry time, and the refresh token.
        """
        # refresh access token
        tkn, expiry, refresh_tkn = await self._refresh(refresh_tkn)

        # update ctx
        self.save_to_ctx(tkn, expiry)

        return tkn, expiry, refresh_tkn

    # ---------------------------------- storage --------------------------------- #

    def save_to_ctx(self, access_token: str, expiry: datetime) -> None:
        """
        Save the access token and its expiry time to the context variable.

        Args:
            access_token (str): The access token.
            expiry (datetime): The expiry time of the access token.
        """
        ctx = deepcopy(_TOKEN_STORE.get())
        client_ctx = {"access_token": access_token, "expiry": expiry}
        ctx.update({self.__integration__: client_ctx})

        _TOKEN_STORE.set(ctx)  # is this step needed?

    async def dump(self, access_token: str, access_token_expiry: datetime, refresh_token: str) -> None:
        """
        Encrypt and persist the tokens in the datastore.

        Args:
            access_token (str): The access token.
            access_token_expiry (datetime): The expiry time of the access token.
            refresh_token (str): The refresh token.

        """

        access_token = self._encryption_service.encrypt(access_token)
        refresh_token = self._encryption_service.encrypt(refresh_token)

        try:
            # -- try accessing --

            await Tokens.get(
                type=TokenType.ACCESS.value,
                tokenable_id=self.tokenable_id,
                tokenable_type=self.__tokenable_type__,
            )

        except DoesNotExist:
            # -- create new entries --

            await Tokens.create(
                token=access_token,
                type=TokenType.ACCESS.value,
                tokenable_type=self.__tokenable_type__,
                tokenable_id=self.tokenable_id,
                expire_at=access_token_expiry,
            )

            await Tokens.create(
                token=refresh_token,
                type=TokenType.REFRESH.value,
                tokenable_type=self.__tokenable_type__,
                tokenable_id=self.tokenable_id,
            )

        else:
            # -- update --

            await Tokens.filter(
                type=TokenType.ACCESS.value,
                tokenable_id=self.tokenable_id,
                tokenable_type=self.__tokenable_type__,
            ).update(
                token=access_token,
                expire_at=access_token_expiry,
            )

            await Tokens.filter(
                type=TokenType.REFRESH.value,
                tokenable_id=self.tokenable_id,
                tokenable_type=self.__tokenable_type__,
            ).update(
                token=refresh_token,
            )

    async def load(self) -> Tuple[str, datetime, str]:
        """
        Load and return decrypted tokens from the datastore.

        Returns:
            Tuple[str, datetime, str]: The access token, its expiry time, and the refresh token.

        Raises:
            CredentialsError: If tokens are not found in the datastore.
        """
        try:
            access_token_row = await Tokens.get(
                type=TokenType.ACCESS.value,
                tokenable_id=self.tokenable_id,
                tokenable_type=self.__tokenable_type__,
            )
            refresh_token_row = await Tokens.get(
                type=TokenType.REFRESH.value,
                tokenable_id=self.tokenable_id,
                tokenable_type=self.__tokenable_type__,
            )
        except DoesNotExist as exc:
            raise CredentialsError("Tokens not found in DB!") from exc

        access_token = access_token_row.token
        expiry = access_token_row.expire_at

        refresh_token = refresh_token_row.token

        access_token = self._encryption_service.decrypt(access_token)
        refresh_token = self._encryption_service.decrypt(refresh_token)

        return access_token, expiry, refresh_token

    # ---------------------------------- utility --------------------------------- #

    @staticmethod
    def _expires_at(expires_in: int) -> datetime:
        return datetime.utcnow() + timedelta(seconds=expires_in)

    @staticmethod
    def _has_expired(expiry: datetime, tolerance: int = 60) -> bool:
        """
        Check if the token has expired, considering a tolerance period.

        Args:
            expiry (datetime): The expiry time of the token.
            tolerance (int, optional): The tolerance period in seconds. Defaults to 600.

        Returns:
            bool: True if the token has expired, False otherwise.
        """
        now = datetime.utcnow()
        now_utc = now.replace(tzinfo=timezone.utc)

        expiry_with_tolerance = expiry - timedelta(seconds=tolerance)
        expiry_with_tolerance_utc = expiry_with_tolerance.replace(tzinfo=timezone.utc)
        return now_utc >= expiry_with_tolerance_utc

    def get_git_actor(self) -> Actor:
        raise NotImplementedError()
