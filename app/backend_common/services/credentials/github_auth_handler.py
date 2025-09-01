from __future__ import annotations

from datetime import datetime
from typing import Tuple

from git.util import Actor
from tortoise.exceptions import DoesNotExist
from typing_extensions import override

from app.backend_common.constants.constants import TokenType
from app.backend_common.exception.exception import CredentialsError
from app.backend_common.models.dao.postgres.tokens import Tokens
from app.backend_common.service_clients.oauth import GithubOAuthClient
from app.backend_common.utils.sanic_wrapper import CONFIG

from .auth_handler import _TOKEN_STORE, AuthHandler


class GithubAuthHandler(AuthHandler):
    __integration__ = "github"
    __tokenable_type__ = "workspace"

    DATETIME_FMT = "%Y-%m-%dT%H:%M:%SZ"

    @override
    def __init__(self, tokenable_id: int | None = None) -> None:
        self.tokenable_id: int | None = tokenable_id

    @override
    async def _authorise(self, installation_id: str) -> Tuple[str, datetime, str]:
        response = await GithubOAuthClient.get_access_token(installation_id)
        access_token = response["token"]
        expires_at = response["expires_at"]

        expires_at = datetime.strptime(expires_at, self.DATETIME_FMT)

        return access_token, expires_at, installation_id

    @override
    async def _refresh(self, installation_id: str) -> Tuple[str, datetime, str]:
        response = await GithubOAuthClient.get_access_token(installation_id)
        access_token = response["token"]
        expires_at = response["expires_at"]

        expires_at = datetime.strptime(expires_at, self.DATETIME_FMT)

        return access_token, expires_at, installation_id

    # ---------------------------------------------------------------------------- #

    @override
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
        tkn, expiry, installation_id = await self.load()

        if not self._has_expired(expiry=expiry):
            # store to ctx
            self.save_to_ctx(tkn, expiry)
            return tkn

        # -- refresh --
        tkn, expiry, installation_id = await self.refresh(installation_id)
        await self.dump(tkn, expiry, installation_id)

        return tkn

    @override
    async def authorise(self, installation_id: str) -> Tuple[str, datetime, str]:
        """
        Get access and refresh tokens from the authorisation server.

        Args:
            auth_code (str): The authorisation code.

        Returns:
            Tuple[str, datetime, str]: The access token, its expiry time, and the refresh token.
        """
        # authorise
        tkn, expiry, refresh_tkn = await self._authorise(installation_id)

        # update ctx
        self.save_to_ctx(tkn, expiry)

        return tkn, expiry, installation_id

    @override
    async def refresh(self, installation_id: str) -> Tuple[str, datetime, str]:
        """
        Use the refresh token to get a fresh access token.

        Args:
            refresh_tkn (str): The refresh token.

        Returns:
            Tuple[str, datetime, str]: The new access token, its expiry time, and the refresh token.
        """
        # refresh access token
        tkn, expiry, installation_id = await self._refresh(installation_id)

        # update ctx
        self.save_to_ctx(tkn, expiry)

        return tkn, expiry, installation_id

    @override
    async def dump(self, access_token: str, access_token_expiry: datetime, installation_id: str) -> None:
        """
        Encrypt and persist the tokens in the datastore.

        Args:
            access_token (str): The access token.
            access_token_expiry (datetime): The expiry time of the access token.
            refresh_token (str): The refresh token.

        """

        if not self.tokenable_id:
            raise CredentialsError("Tokenable Id is not set")

        access_token = self._encryption_service.encrypt(access_token)
        installation_id = self._encryption_service.encrypt(installation_id)

        try:
            # -- try to access --

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
                token=installation_id,
                type=TokenType.INSTALLATION.value,
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
                type=TokenType.INSTALLATION.value,
                tokenable_id=self.tokenable_id,
                tokenable_type=self.__tokenable_type__,
            ).update(
                token=installation_id,
            )

    @override
    async def load(self) -> Tuple[str, datetime, str]:
        """
        Load and return decrypted tokens from the datastore.

        Returns:
            Tuple[str, datetime, str]: The access token, its expiry time, and the refresh token.

        Raises:
            CredentialsError: If tokens are not found in the datastore.
        """

        if not self.tokenable_id:
            raise CredentialsError("Tokenable Id is not set")

        try:
            access_token_row = await Tokens.get(
                type=TokenType.ACCESS.value,
                tokenable_id=self.tokenable_id,
                tokenable_type=self.__tokenable_type__,
            )
            installation_id_row = await Tokens.get(
                type=TokenType.INSTALLATION.value,
                tokenable_id=self.tokenable_id,
                tokenable_type=self.__tokenable_type__,
            )
        except DoesNotExist as exc:
            raise CredentialsError("Tokens not found in DB") from exc

        access_token = access_token_row.token
        expiry = access_token_row.expire_at

        installation_id = installation_id_row.token

        access_token = self._encryption_service.decrypt(access_token)
        installation_id = self._encryption_service.decrypt(installation_id)

        return access_token, expiry, installation_id

    @override
    def get_git_actor(self) -> Actor:
        return Actor(
            name=CONFIG.config["GIT_ACTORS"]["GITHUB"]["NAME"],
            email=CONFIG.config["GIT_ACTORS"]["GITHUB"]["EMAIL"],
        )
