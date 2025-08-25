import json
from datetime import datetime
from typing import List, Optional

from sanic.log import logger

from app.backend_common.constants.past_workflows import SessionStatus
from app.backend_common.models.dao.postgres.message_sessions import MessageSession
from app.backend_common.models.dto.message_sessions_dto import (
    MessageSessionData,
    MessageSessionDTO,
)
from app.backend_common.repository.db import DB


class MessageSessionsRepository:
    @classmethod
    async def get_by_id(
        cls,
        session_id: int,
    ) -> Optional[MessageSessionDTO]:
        try:
            message_session = await DB.by_filters(
                model_name=MessageSession,
                where_clause={"id": session_id},
                fetch_one=True,
            )
            if not message_session:
                return None
            return MessageSessionDTO(**message_session)

        except Exception as ex:
            logger.error(
                f"error occurred while fetching message_threads from db for session_id filters : {session_id}, ex: {ex}"
            )
            raise ex

    @classmethod
    async def create_message_session(cls, message_session_data: MessageSessionData) -> MessageSessionDTO:
        try:
            message_sesison = await DB.create(MessageSession, message_session_data.model_dump(mode="json"))
            return MessageSessionDTO.model_validate_json(
                json_data=json.dumps(
                    dict(
                        id=message_sesison.id,
                        user_team_id=message_sesison.user_team_id,
                        client=message_sesison.client,
                        client_version=message_sesison.client_version,
                        summary=message_sesison.summary,
                        created_at=message_sesison.created_at.isoformat(),
                        updated_at=message_sesison.updated_at.isoformat(),
                        session_type=message_sesison.session_type,
                    )
                )
            )

        except Exception as ex:
            logger.error(
                f"error occurred while creating message_thread in db for message_thread_data : {message_session_data}, ex: {ex}"
            )
            raise ex

    @classmethod
    async def update_session_summary(cls, session_id: int, summary: str) -> None:
        try:
            await DB.update_by_filters(None, MessageSession, {"summary": summary}, {"id": session_id})
        except Exception as ex:
            logger.error(f"error occurred while updating message_session in DB, ex: {ex}")
            raise ex

    @classmethod
    async def get_message_sessions_ids(
        cls,
        user_team_id: int,
        session_type: Optional[str] = None,
    ) -> List[int]:  # Change the return type to List[int] for session IDs
        try:
            filters = {"user_team_id": user_team_id, "session_type": session_type}
            message_sessions = await DB.by_filters(
                model_name=MessageSession,
                where_clause=filters,
                fetch_one=False,
            )
            if not message_sessions:
                return []

            # Return only the IDs of the message sessions
            return [message_session["id"] for message_session in message_sessions]

        except Exception as ex:  # noqa: BLE001
            logger.error(
                f"error occurred while fetching message_sessions from db for user_team_id filters : {user_team_id}, ex: {ex}"
            )
            return []

    @classmethod
    async def get_message_sessions_by_user_team_id(
        cls,
        user_team_id: int,
        session_type: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[MessageSessionDTO]:
        if not limit:
            limit = 10
        if not offset:
            offset = 0
        try:
            filters = {
                "user_team_id": user_team_id,
                "status": SessionStatus.ACTIVE.value,
            }
            if session_type:
                filters["session_type"] = session_type

            message_sessions = await DB.by_filters(
                model_name=MessageSession,
                where_clause=filters,
                fetch_one=False,
                limit=limit,
                offset=offset,
                order_by=["-updated_at"],
            )
            if not message_sessions:
                return []
            return [MessageSessionDTO(**message_session) for message_session in message_sessions]

        except Exception as ex:  # noqa: BLE001
            logger.error(
                f"error occurred while fetching message_sessions from db for user_team_id filters : {user_team_id}, ex: {ex}"
            )
            return []

    @classmethod
    async def soft_delete_message_session_by_id(cls, session_id: int, user_team_id: int) -> None:
        try:
            # First check if the session belongs to the user
            message_session = await DB.by_filters(
                model_name=MessageSession,
                where_clause={"id": session_id, "user_team_id": user_team_id},
                fetch_one=True,
            )
            if not message_session:
                raise ValueError("Session not found or you don't have permission to delete it")

            # Soft delete the session
            await DB.update_by_filters(
                None,
                MessageSession,
                {"status": SessionStatus.DELETED.value, "deleted_at": datetime.now()},
                {"id": session_id},
            )
        except (ValueError, Exception) as ex:
            logger.error(f"error occurred while soft deleting message_session in DB, ex: {ex}")
            raise ex
