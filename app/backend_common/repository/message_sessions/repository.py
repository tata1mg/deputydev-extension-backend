from datetime import datetime
from typing import Dict, List, Optional

from sanic.log import logger

from app.backend_common.models.dao.postgres.message_sessions import MessageSessions
from app.backend_common.models.dto.message_sessions_dto import MessageSessionData, MessageSessionDTO
from app.backend_common.repository.db import DB


class MessageSessionsRepository:
    @classmethod
    async def get_message_sessions(cls, user_team_id: str) -> List[MessageSessionDTO]:
        try:
            message_sessions = await DB.by_filters(
                model_name=MessageSessions,
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