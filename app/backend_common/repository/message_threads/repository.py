from typing import Dict, List, Optional, Union

from sanic.log import logger

from app.backend_common.models.dao.postgres.message_threads import MessageThread
from app.backend_common.models.dto.message_thread_dto import (
    MessageThreadData,
    MessageThreadDTO,
)
from app.backend_common.repository.db import DB


class MessageThreadsRepository:
    @classmethod
    async def get_message_threads_for_session(
        cls, session_id: int, content_hashes: List[str] = []
    ) -> List[MessageThreadDTO]:
        try:
            filters: Dict[str, Union[List[str], int]] = {"session_id": session_id}
            if content_hashes:
                filters["data_hash__in"] = content_hashes
            message_threads = await DB.by_filters(
                model_name=MessageThread,
                where_clause=filters,
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

    @classmethod
    async def bulk_insert_message_threads(cls, message_thread_datas: List[MessageThreadData]) -> List[MessageThreadDTO]:
        try:
            message_threads = [
                message_thread_data.model_dump(mode="json") for message_thread_data in message_thread_datas
            ]
            return await DB.bulk_create(MessageThread, message_threads)
        except Exception as ex:
            logger.error(
                f"error occurred while creating message_thread in db for message_thread_data : {message_thread_datas}, ex: {ex}"
            )
            return []

    @classmethod
    async def get_message_threads_by_ids(cls, message_thread_ids: List[int]) -> List[MessageThreadDTO]:
        try:
            message_threads = await DB.by_filters(
                model_name=MessageThread,
                where_clause={"id__in": message_thread_ids},
                fetch_one=False,
            )
            if not message_threads:
                return []
            return [MessageThreadDTO(**message_thread) for message_thread in message_threads]

        except Exception as ex:
            logger.error(
                f"error occurred while fetching message_threads from db for message_thread_ids filters : {message_thread_ids}, ex: {ex}"
            )
            return []
