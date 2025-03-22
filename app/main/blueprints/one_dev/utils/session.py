# wrapper to get session ID from headers or add one if not present
from functools import wraps
from typing import Any, Optional

from torpedo import Request

from app.backend_common.models.dto.message_sessions_dto import MessageSessionData
from app.backend_common.repository.message_sessions.repository import (
    MessageSessionsRepository,
)
from app.main.blueprints.one_dev.utils.client.dataclasses.main import ClientData
from app.main.blueprints.one_dev.utils.dataclasses.main import AuthData


async def check_or_create_session(session_type: str, client_data: ClientData, auth_data: AuthData, sesison_id: Optional[int] = None) -> int:
    final_session_id = sesison_id
    if not final_session_id:
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
        final_session_id = message_session.id
    return final_session_id

def ensure_session_id(session_type: str = "MESSAGE") -> Any:
    def _ensure_session_id(func: Any) -> Any:
        """
        Wrapper to ensure a session ID is present in the request headers.
        """

        @wraps(func)
        async def wrapper(_request: Request, client_data: ClientData, auth_data: AuthData, **kwargs: Any) -> Any:
            # Check if the session ID is present in the headers
            session_id = _request.headers.get("X-Session-ID")
            session_id = await check_or_create_session(session_type, client_data, auth_data, session_id)
            # Proceed to the wrapped function
            return await func(_request, client_data=client_data, auth_data=auth_data, session_id=session_id, **kwargs)

        return wrapper

    return _ensure_session_id
