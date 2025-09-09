from typing import Optional

from app.backend_common.repository.chat_attachments.repository import ChatAttachmentsRepository
from deputydev_core.llm_handler.interfaces.repositories_interface import ChatAttachmentsRepositoryInterface
from deputydev_core.llm_handler.models.dto.chat_attachments_dto import ChatAttachmentsDTO


class ChatAttachmentsRepositoryAdapter(ChatAttachmentsRepositoryInterface):
    """Adapter that wraps your existing ChatAttachmentsRepository"""

    def __init__(self, repository: ChatAttachmentsRepository) -> None:
        self.repository = repository

    async def get_attachment_by_id(self, attachment_id: int) -> Optional[ChatAttachmentsDTO]:
        return await self.repository.get_attachment_by_id(attachment_id)
