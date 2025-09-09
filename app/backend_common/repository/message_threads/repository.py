import json
from typing import Dict, List, Optional, Union

from sanic.log import logger

from app.backend_common.models.dao.postgres.message_threads import MessageThread
from app.backend_common.repository.db import DB
from deputydev_core.llm_handler.models.dto.message_thread_dto import (
    MessageCallChainCategory,
    MessageThreadActor,
    MessageThreadData,
    MessageThreadDTO,
    MessageType,
)


class MessageThreadsRepository:
    @classmethod
    async def get_message_thread_by_id(cls, message_thread_id: int) -> Optional[MessageThreadDTO]:
        try:
            message_thread = await DB.by_filters(
                model_name=MessageThread,
                where_clause={"id": message_thread_id},
                fetch_one=True,
            )
            if not message_thread:
                return None
            return MessageThreadDTO(**message_thread)
        except Exception as ex:
            logger.error(
                f"error occurred while getting message_thread in db for message_thread_id : {message_thread_id}, ex: {ex}"
            )
            raise ex

    @classmethod
    async def get_message_threads_for_session(
        cls,
        session_id: int,
        call_chain_category: MessageCallChainCategory,
        content_hashes: List[str] = [],
        prompt_types: List[str] = [],
    ) -> List[MessageThreadDTO]:
        try:
            filters: Dict[str, Union[List[str], int, str]] = {
                "session_id": session_id,
                "call_chain_category": call_chain_category.value,
            }
            if content_hashes:
                filters["data_hash__in"] = content_hashes
            if prompt_types:
                filters["prompt_type__in"] = prompt_types
            message_threads = await DB.by_filters(
                model_name=MessageThread,
                where_clause=filters,
                fetch_one=False,
                order_by=["id"],
            )
            if not message_threads:
                return []
            return [MessageThreadDTO(**message_thread) for message_thread in message_threads]

        except Exception as ex:  # noqa: BLE001
            logger.error(
                f"error occurred while fetching message_threads from db for session_id filters : {session_id}, ex: {ex}"
            )
            return []

    @classmethod
    async def create_message_thread(cls, message_thread_data: MessageThreadData) -> MessageThreadDTO:
        try:
            message_thread = await DB.create(MessageThread, message_thread_data.model_dump(mode="json"))
            return MessageThreadDTO.model_validate_json(
                json_data=json.dumps(
                    dict(
                        id=message_thread.id,
                        session_id=message_thread.session_id,
                        message_data=message_thread.message_data,
                        data_hash=message_thread.data_hash,
                        created_at=message_thread.created_at.isoformat(),
                        updated_at=message_thread.updated_at.isoformat(),
                        actor=message_thread.actor,
                        query_id=message_thread.query_id,
                        message_type=message_thread.message_type,
                        conversation_chain=message_thread.conversation_chain,
                        usage=message_thread.usage,
                        cost=message_thread.cost,
                        llm_model=message_thread.llm_model,
                        prompt_type=message_thread.prompt_type,
                        prompt_category=message_thread.prompt_category,
                        call_chain_category=message_thread.call_chain_category,
                        metadata=message_thread.metadata,
                    )
                )
            )

        except Exception as ex:
            logger.error(
                f"error occurred while creating message_thread in db for message_thread_data : {message_thread_data}, ex: {ex}"
            )
            raise ex

    @classmethod
    async def bulk_insert_message_threads(cls, message_thread_datas: List[MessageThreadData]) -> List[MessageThreadDTO]:
        try:
            message_threads = [
                message_thread_data.model_dump(mode="json") for message_thread_data in message_thread_datas
            ]
            return await DB.bulk_create(MessageThread, message_threads)
        except Exception as ex:  # noqa: BLE001
            logger.error(
                f"error occurred while creating message_thread in db for message_thread_data : {message_thread_datas}, ex: {ex}"
            )
            return []

    @classmethod
    async def get_message_threads_by_ids(cls, message_thread_ids: List[int]) -> List[MessageThreadDTO]:
        """
        Get message threads by message_thread_ids
        Returned message threads are sorted by the order of message_thread_ids
        """
        try:
            message_threads = await DB.by_filters(
                model_name=MessageThread,
                where_clause={"id__in": message_thread_ids},
                fetch_one=False,
            )
            if not message_threads:
                return []
            message_threads = [MessageThreadDTO(**message_thread) for message_thread in message_threads]
            message_threads.sort(key=lambda x: message_thread_ids.index(x.id))
            return message_threads
        except Exception as ex:  # noqa: BLE001
            logger.error(
                f"error occurred while fetching message_threads from db for message_thread_ids filters : {message_thread_ids}, ex: {ex}"
            )
            return []

    @classmethod
    async def get_total_user_queries(cls, session_ids: List[int], call_chain_category: MessageCallChainCategory) -> int:
        try:
            return await DB.count_by_filters(
                model_name=MessageThread,
                filters={
                    "session_id__in": session_ids,
                    "call_chain_category": call_chain_category.value,
                    "actor": MessageThreadActor.USER.value,
                    "message_type": MessageType.QUERY.value,
                },
            )
        except Exception as ex:  # noqa: BLE001
            logger.error(f"error occurred while fetching user queries count for session_ids: {session_ids}, ex: {ex}")
            return 0

    @classmethod
    async def mark_as_migrated(cls, message_thread_ids: List[int]) -> None:
        # add migrated in metadata
        try:
            await DB.update_by_filters(
                None,
                MessageThread,
                {"migrated": True},
                {"id__in": message_thread_ids},
            )
        except Exception as ex:
            logger.error(
                f"error occurred while marking message threads as migrated for message_thread_ids: {message_thread_ids}, ex: {ex}"
            )
            raise ex

    @classmethod
    async def get_unmigrated_threads(
        cls,
        session_id: int,
        call_chain_category: MessageCallChainCategory,
        content_hashes: List[str] = [],
        prompt_types: List[str] = [],
    ) -> List[MessageThreadDTO]:
        try:
            filters: Dict[str, Union[List[str], int, str]] = {
                "session_id": session_id,
                "call_chain_category": call_chain_category.value,
            }
            if content_hashes:
                filters["data_hash__in"] = content_hashes
            if prompt_types:
                filters["prompt_type__in"] = prompt_types

            filters["migrated"] = None
            message_threads = await DB.by_filters(
                model_name=MessageThread,
                where_clause=filters,
                fetch_one=False,
                order_by=["id"],
            )
            if not message_threads:
                return []
            return [MessageThreadDTO(**message_thread) for message_thread in message_threads]

        except Exception as ex:  # noqa: BLE001
            logger.error(
                f"error occurred while fetching message_threads from db for session_id filters : {session_id}, ex: {ex}"
            )
            return []
