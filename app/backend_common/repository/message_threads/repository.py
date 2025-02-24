from typing import List, Optional

from sanic.log import logger

from app.backend_common.models.dao.postgres.message_threads import MessageThread
from app.backend_common.models.dto.message_thread_dto import MessageThreadData, MessageThreadDTO
from app.backend_common.repository.db import DB


class MessageThreadsRepository:
    @classmethod
    async def get_message_threads_for_session(cls, session_id: str) -> List[MessageThreadDTO]:
        try:
            message_threads = await DB.by_filters(
                model_name=MessageThread,
                where_clause={"session_id": session_id},
                fetch_one=False,
            )
            if not message_threads:
                return []
            return [MessageThreadDTO(**message_thread) for message_thread in message_threads]

        except Exception as ex:
            logger.error(
                f"error occurred while fetching message_threads from db for session_id filters : {session_id}, ex: {ex}"
            )
            return []

    @classmethod
    async def create_message_thread(cls, message_thread_data: MessageThreadData) -> Optional[MessageThreadDTO]:
        try:
            message_thread = await DB.create(MessageThread, message_thread_data.model_dump(mode="json"))
            return MessageThreadDTO(**message_thread)

        except Exception as ex:
            logger.error(
                f"error occurred while creating message_thread in db for message_thread_data : {message_thread_data}, ex: {ex}"
            )
            return None
