"""Torpedo Exception Classes."""

from __future__ import annotations

import typing as t

from app.backend_common.utils.sanic_wrapper.constants.http import HTTPStatusCodes


class BaseTorpedoException(Exception):
    """Base Torpedo Exception.

    Attributes:
        error (str): The error message associated with the exception.
        status_code (int): The HTTP status code representing the error. Defaults to 400 (Bad Request).
        meta (Any): Optional metadata associated with the exception.
        error_id (Any): Optional identifier for the specific error instance.
                        This is used with `error_content` dict set in app context.
        sentry_raise (bool): Whether to raise the exception to Sentry. Defaults to True.

    Note:
        This class serves as a base exception for the Torpedo services. It is recommended
        to extend this class when creating custom exceptions for specific use cases within the service.

    """  # noqa : E501

    def __init__(
        self,
        error: str,
        status_code: int = HTTPStatusCodes.BAD_REQUEST.value,
        meta: t.Any = None,
        quiet: bool = True,
        error_id: t.Any = None,
        error_code: int | None = None,
        code: t.Any = None,
        sentry_raise: bool = True,
    ) -> None:
        self._error: str = error
        self._status_code: int = status_code
        self._meta = meta
        self._quiet: bool = quiet
        self._id = error_id
        self._code = code
        self._error_code = error_code
        self._sentry_raise: bool = sentry_raise

    @property
    def error(self) -> str:
        """Error message."""
        return self._error

    @property
    def status_code(self) -> int:
        """Exception status code."""
        return self._status_code

    @property
    def meta(self) -> t.Any:
        """Attached meta information."""
        return self._meta

    @property
    def quiet(self) -> bool:
        """Not used internally by torpedo."""
        return self._quiet

    @property
    def error_id(self) -> t.Any:
        """Exception error id."""
        return self._id

    @property
    def error_code(self) -> int | None:
        """Exception error code."""
        return self._error_code

    @property
    def code(self) -> t.Any:
        """Not used internally by torpedo."""
        return self._code

    @property
    def sentry_raise(self) -> bool:
        """Whether to raise excpetion to sentry."""
        return self._sentry_raise


BaseSanicException = BaseTorpedoException
"""Aliased for backward compatibility."""


class TaskExecutorException(BaseTorpedoException):
    def __init__(
        self,
        error: str,
        status_code: int = HTTPStatusCodes.BAD_REQUEST.value,
        meta: t.Any = None,
        quiet: bool = True,
        sentry_raise: bool = True,
    ):
        super().__init__(error, status_code, meta, quiet, sentry_raise=sentry_raise)


class InterServiceRequestException(BaseTorpedoException):
    def __init__(
        self,
        error: str,
        status_code: int = HTTPStatusCodes.BAD_REQUEST.value,
        meta: t.Any = None,
        quiet: bool = True,
        code: t.Any = None,
        error_id: t.Any = None,
        error_code: int | None = None,
        sentry_raise: bool = True,
        custom_http_codes_mapping_enabled: bool = True,
    ):
        self.custom_http_codes_mapping_enabled = custom_http_codes_mapping_enabled
        super().__init__(
            error,
            status_code,
            meta,
            quiet,
            error_id,
            error_code,
            code,
            sentry_raise=sentry_raise,
        )


HTTPInterServiceRequestException = InterServiceRequestException
"""Aliased for backward compatibility."""


class HTTPRequestException(BaseTorpedoException):
    def __init__(
        self,
        error: str,
        status_code: int = HTTPStatusCodes.INTERNAL_SERVER_ERROR.value,
        meta: t.Any = None,
        quiet: bool = True,
        error_code: int | None = None,
        sentry_raise: bool = True,
    ):
        super().__init__(error, status_code, meta, quiet, error_code, sentry_raise=sentry_raise)


class HTTPRequestTimeoutException(BaseTorpedoException):
    def __init__(
        self,
        error: str,
        status_code: int = HTTPStatusCodes.REQUEST_TIMEOUT.value,
        meta: t.Any = None,
        quiet: bool = True,
        error_code: int | None = None,
        sentry_raise: bool = True,
    ):
        super().__init__(error, status_code, meta, quiet, error_code, sentry_raise=sentry_raise)


class BadRequestException(BaseTorpedoException):
    def __init__(
        self,
        error: str,
        status_code: int = HTTPStatusCodes.BAD_REQUEST.value,
        meta: t.Any = None,
        quiet: bool = True,
        error_id: t.Any = None,
        error_code: int | None = None,
        sentry_raise: bool = True,
    ):
        super().__init__(
            error,
            status_code,
            meta,
            quiet,
            error_id,
            error_code,
            sentry_raise=sentry_raise,
        )


class JsonDecodeException(BaseTorpedoException):
    def __init__(
        self,
        error: str,
        status_code: int = HTTPStatusCodes.INTERNAL_SERVER_ERROR.value,
        meta: t.Any = None,
        quiet: bool = True,
        error_code: int | None = None,
        sentry_raise: bool = True,
    ):
        super().__init__(error, status_code, meta, quiet, error_code, sentry_raise=sentry_raise)


class ForbiddenException(BaseTorpedoException):
    def __init__(
        self,
        error: str,
        status_code: int = HTTPStatusCodes.FORBIDDEN.value,
        meta: t.Any = None,
        quiet: bool = True,
        error_code: int | None = None,
        sentry_raise: bool = True,
        custom_http_codes_mapping_enabled: bool = True,
    ):
        self.custom_http_codes_mapping_enabled = custom_http_codes_mapping_enabled
        super().__init__(error, status_code, meta, quiet, error_code, sentry_raise=sentry_raise)


class NotFoundException(BaseTorpedoException):
    def __init__(
        self,
        error: str,
        status_code: int = HTTPStatusCodes.NOT_FOUND.value,
        meta: t.Any = None,
        quiet: bool = True,
        error_id: t.Any = None,
        error_code: int | None = None,
        sentry_raise: bool = True,
        custom_http_codes_mapping_enabled: bool = True,
    ):
        self.custom_http_codes_mapping_enabled = custom_http_codes_mapping_enabled
        super().__init__(
            error,
            status_code,
            meta,
            quiet,
            error_id,
            error_code,
            sentry_raise=sentry_raise,
        )


class OpenCircuitException(BaseTorpedoException):
    def __init__(
        self,
        error: str,
        status_code: int = HTTPStatusCodes.SERVICE_UNAVAILABLE.value,
        meta: t.Any = None,
        quiet: bool = True,
        error_id: t.Any = None,
        error_code: int | None = None,
        sentry_raise: bool = True,
        custom_http_codes_mapping_enabled: bool = True,
    ):
        self.custom_http_codes_mapping_enabled = custom_http_codes_mapping_enabled
        super().__init__(
            error,
            status_code,
            meta,
            quiet,
            error_id,
            error_code,
            sentry_raise=sentry_raise,
        )


class StartupException(BaseTorpedoException):
    """Service startup related errors."""
