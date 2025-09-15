from typing import List

from deputydev_core.llm_handler.interfaces.repositories_interface import MessageThreadsRepositoryInterface
from deputydev_core.llm_handler.models.dto.message_thread_dto import (
    MessageCallChainCategory,
    MessageThreadData,
    MessageThreadDTO,
)

from app.backend_common.repository.message_threads.repository import MessageThreadsRepository


class MessageThreadsRepositoryAdapter(MessageThreadsRepositoryInterface):
    """Adapter that wraps your existing MessageThreadsRepository"""

    def __init__(self, repository: MessageThreadsRepository) -> None:
        self.repository = repository

    async def create_message_thread(self, data: MessageThreadData) -> MessageThreadDTO:
        return await self.repository.create_message_thread(data)

    async def get_message_threads_for_session(
        self, session_id: int, call_chain_category: MessageCallChainCategory
    ) -> List[MessageThreadDTO]:
        return await self.repository.get_message_threads_for_session(session_id, call_chain_category)

    async def bulk_insert_message_threads(self, data: List[MessageThreadData]) -> List[MessageThreadDTO]:
        return await self.repository.bulk_insert_message_threads(data)

    async def get_message_threads_by_ids(self, ids: List[int]) -> List[MessageThreadDTO]:
        return await self.repository.get_message_threads_by_ids(ids)
