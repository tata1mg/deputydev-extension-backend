import json
from typing import Optional

from sanic.log import logger

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
    async def get_message_sessions(cls, user_team_id: str) -> List[MessageSessionDTO]:
        try:
            message_sessions = await DB.by_filters(
                model_name=MessageSession,
                where_clause={"user_team_id": user_team_id},
                fetch_one=False,
            )
            if not message_sessions:
                return []
            return [MessageSessionDTO(**message_session) for message_session in message_sessions]

        except Exception as ex:
            logger.error(
                f"error occurred while fetching message_sessions from db for user_team_id filters : {user_team_id}, ex: {ex}"
            )
            return []