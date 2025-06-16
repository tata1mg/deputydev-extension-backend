from typing import Optional

from sanic.log import logger

from app.backend_common.models.dao.postgres.chat_attachments import ChatAttachments
from app.backend_common.models.dto.chat_attachments_dto import ChatAttachmentsData, ChatAttachmentsDTO
from app.backend_common.repository.db import DB


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
    async def store_new_attachment(cls, chat_attachment_data: ChatAttachmentsData) -> ChatAttachmentsDTO:
        try:
            new_data = await DB.create(model=ChatAttachments, payload=chat_attachment_data.model_dump(mode="json"))
            if not new_data:
                raise Exception("Failed to create new chat_attachment in db")
            return ChatAttachmentsDTO(
                id=new_data.id,
                s3_key=new_data.s3_key,
                file_name=new_data.file_name,
                file_type=new_data.file_type,
                status=new_data.status,
                created_at=new_data.created_at,
                updated_at=new_data.updated_at,
            )
        except Exception as ex:
            logger.error(
                f"error occurred while creating/updating chat_attachment in db for data : {chat_attachment_data.model_dump(mode='json')}, ex: {ex}"
            )
            raise ex

    @classmethod
    async def update_attachment_status(cls, attachment_id: int, status: str) -> Optional[ChatAttachmentsDTO]:
        try:
            await DB.update_by_filters(
                row=None,
                model_name=ChatAttachments,
                where_clause={"id": attachment_id},
                payload={"status": status},
            )
        except Exception as ex:
            logger.error(
                f"error occurred while updating chat_attachment status in db for id : {attachment_id}, ex: {ex}"
            )
            raise ex
