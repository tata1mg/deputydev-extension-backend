from typing import Optional

from sanic.log import logger

from app.backend_common.repository.db import DB
from app.backend_common.models.dao.postgres.chat_attachments import ChatAttachments
from app.backend_common.models.dto.chat_attachments_dto import ChatAttachmentsDTO, ChatAttachmentsData


class ChatAttachmentsRepository:
    @classmethod
    async def get_attachment_by_id(cls, attachment_id: int) -> Optional[ChatAttachmentsDTO]:
        try:
            attachment = await DB.by_filters(
                model_name=ChatAttachments,
                where_clause={"id": attachment_id},
                fetch_one=True,
            )
            if not attachment:
                return None
            return ChatAttachmentsDTO(**attachment)
        except Exception as ex:
            logger.error(f"error occurred while getting chat_attachment in db for id : {attachment_id}, ex: {ex}")
            raise ex

    @classmethod
    async def store_new_attachment(cls, chat_attachment_data: ChatAttachmentsData):
        try:
            await DB.create(model=ChatAttachments, payload=chat_attachment_data.model_dump(mode="json"))
        except Exception as ex:
            logger.error(
                f"error occurred while creating/updating chat_attachment in db for data : {chat_attachment_data.model_dump(mode='json')}, ex: {ex}"
            )
            raise ex
