# wrapper to get session ID from headers or add one if not present
from functools import wraps
from typing import Any, Optional

from deputydev_core.utils.app_logger import AppLogger

from app.backend_common.models.dto.message_sessions_dto import (
    MessageSessionData,
    MessageSessionDTO,
)
from app.backend_common.repository.message_sessions.repository import (
    MessageSessionsRepository,
)
from app.backend_common.utils.dataclasses.main import AuthData, ClientData
from app.backend_common.utils.sanic_wrapper import Request
from app.backend_common.utils.sanic_wrapper.exceptions import BadRequestException


async def get_stored_session(session_id: Optional[int] = None) -> Optional[MessageSessionDTO]:
    """
    Check if the session ID is valid.
    """
    if not session_id:
        return None

    try:
        session = await MessageSessionsRepository.get_by_id(session_id=session_id)
        return session
    except Exception as _ex:  # noqa: BLE001
        AppLogger.log_error(f"Error occurred while fetching session from DB: {str(_ex)}")
        return None


async def create_new_session(session_type: str, client_data: ClientData, auth_data: AuthData) -> MessageSessionDTO:
    # get the client and client version from the headers
    client = client_data.client
    client_version = client_data.client_version

    # Generate a new session entry
    message_session = await MessageSessionsRepository.create_message_session(
        MessageSessionData(
            user_team_id=auth_data.user_team_id,
            client=client,
            client_version=client_version,
            session_type=session_type,
        )
    )
    return message_session


async def get_valid_session_data(
    _request: Request, client_data: ClientData, auth_data: AuthData, auto_create: bool = False
) -> MessageSessionDTO:
    session_id: Optional[str] = _request.headers.get("X-Session-ID")
    session_type: Optional[str] = _request.headers.get("X-Session-Type")

    # check if the session ID is valid
    valid_session_data = await get_stored_session(session_id)

    # If the session data is not valid, create a new session, if auto_create is set to True
    if not valid_session_data:
        if auto_create:
            try:
                if not session_type or not isinstance(session_type, str) or not session_type.strip():
                    raise BadRequestException("Invalid session type provided while creating a new session")
                valid_session_data = await create_new_session(session_type, client_data, auth_data)
            except Exception as _ex:  # noqa: BLE001
                AppLogger.log_error(f"Error occurred while creating a new session: {str(_ex)}")
                raise BadRequestException(f"Failed to create a new session: {str(_ex)}")
        else:
            raise BadRequestException("Invalid session ID")

    return valid_session_data


def ensure_session_id(auto_create: bool = False) -> Any:
    def _ensure_session_id(func: Any) -> Any:
        """
        Wrapper to ensure a session ID is present in the request headers.
        """

        @wraps(func)
        async def wrapper(_request: Request, *args: Any, **kwargs: Any) -> Any:
            client_data: ClientData = kwargs.get("client_data")
            auth_data: AuthData = kwargs.get("auth_data")

            valid_session_data = await get_valid_session_data(
                _request=_request,
                client_data=client_data,
                auth_data=auth_data,
                auto_create=auto_create,
            )
            kwargs = {
                **kwargs,
                "session_id": valid_session_data.id,
            }
            # Proceed to the wrapped function
            return await func(_request, *args, **kwargs)

        return wrapper

    return _ensure_session_id
