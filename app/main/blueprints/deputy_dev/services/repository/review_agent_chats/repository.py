from typing import List, Optional

from sanic.log import logger

from app.backend_common.repository.db import DB
from app.main.blueprints.deputy_dev.models.dao.postgres.review_agent_chats import AgentChats
from app.main.blueprints.deputy_dev.models.dto.review_agent_chats_dto import (
    ActorType,
    MessageType,
    ReviewAgentChatCreateRequest,
    ReviewAgentChatDTO,
    ReviewAgentChatUpdateRequest,
)


class ReviewAgentChatsRepository:
    @classmethod
    async def get_chats_by_session_id(cls, session_id: int) -> List[ReviewAgentChatDTO]:
        """
        Fetch all chats for a given session_id, ordered by creation time.
        """
        try:
            chats = await DB.by_filters(
                model_name=AgentChats,
                where_clause={"session_id": session_id},
                fetch_one=False,
                order_by="created_at",
            )
            if not chats:
                return []
            return [ReviewAgentChatDTO(**chat) for chat in chats]
        except Exception as ex:
            logger.error(f"Error occurred while fetching review agent chats for session_id: {session_id}, ex: {ex}")
            raise ex

    @classmethod
    async def get_chat_by_id(cls, chat_id: int) -> Optional[ReviewAgentChatDTO]:
        """
        Fetch a specific chat by its ID.
        """
        try:
            chat = await DB.by_filters(
                model_name=AgentChats,
                where_clause={"id": chat_id},
                fetch_one=True,
            )
            if not chat:
                return None
            return ReviewAgentChatDTO(**chat)
        except Exception as ex:
            logger.error(f"Error occurred while fetching review agent chat by id: {chat_id}, ex: {ex}")
            raise ex

    @classmethod
    async def create_chat(cls, chat_data: ReviewAgentChatCreateRequest) -> ReviewAgentChatDTO:
        """
        Create a new chat entry.
        """
        try:
            payload = chat_data.model_dump(mode="json")
            created_chat = await DB.create(AgentChats, payload)
            return ReviewAgentChatDTO(**await created_chat.to_dict())
        except Exception as ex:
            logger.error(
                f"Error occurred while creating review agent chat for session_id: {chat_data.session_id}, ex: {ex}"
            )
            raise ex

    @classmethod
    async def update_chat(cls, chat_id: int, update_data: ReviewAgentChatUpdateRequest) -> Optional[ReviewAgentChatDTO]:
        """
        Update an existing chat entry.
        """
        try:
            # Only include fields that are not None
            payload = {k: v for k, v in update_data.model_dump(mode="json").items() if v is not None}

            if not payload:
                # No fields to update, return existing chat
                return await cls.get_chat_by_id(chat_id)

            updated_fields = list(payload.keys()) + ["updated_at"]

            await DB.update_with_filters(
                None,
                model=AgentChats,
                payload=payload,
                where_clause={"id": chat_id},
                update_fields=updated_fields,
            )

            return await cls.get_chat_by_id(chat_id)
        except Exception as ex:
            logger.error(f"Error occurred while updating review agent chat id: {chat_id}, ex: {ex}")
            raise ex

    @classmethod
    async def delete_chat(cls, chat_id: int) -> bool:
        """
        Delete a chat entry by ID.
        """
        try:
            await DB.delete_with_filters(model=AgentChats, where_clause={"id": chat_id})
            return True
        except Exception as ex:
            logger.error(f"Error occurred while deleting review agent chat id: {chat_id}, ex: {ex}")
            raise ex

    @classmethod
    async def get_latest_chats_by_session_id(cls, session_id: int, limit: int = 50) -> List[ReviewAgentChatDTO]:
        """
        Fetch the latest N chats for a given session_id, ordered by creation time (newest first).
        """
        try:
            chats = await DB.by_filters(
                model_name=AgentChats,
                where_clause={"session_id": session_id},
                fetch_one=False,
                order_by="-created_at",
                limit=limit,
            )
            if not chats:
                return []
            # Reverse to get chronological order
            chats.reverse()
            return [ReviewAgentChatDTO(**chat) for chat in chats]
        except Exception as ex:
            logger.error(
                f"Error occurred while fetching latest review agent chats for session_id: {session_id}, ex: {ex}"
            )
            raise ex

    @classmethod
    async def get_chats_by_actor_and_session(cls, session_id: int, actor: ActorType) -> List[ReviewAgentChatDTO]:
        """
        Fetch chats by session_id and actor type (REVIEW_AGENT/ASSISTANT).
        """
        try:
            chats = await DB.by_filters(
                model_name=AgentChats,
                where_clause={"session_id": session_id, "actor": actor.value},
                fetch_one=False,
                order_by="created_at",
            )
            if not chats:
                return []
            return [ReviewAgentChatDTO(**chat) for chat in chats]
        except Exception as ex:
            logger.error(
                f"Error occurred while fetching review agent chats for session_id: {session_id}, actor: {actor.value}, ex: {ex}"
            )
            raise ex

    @classmethod
    async def get_chats_by_message_type_and_session(
        cls, session_id: int, message_type: MessageType
    ) -> List[ReviewAgentChatDTO]:
        """
        Fetch chats by session_id and message type (TEXT/TOOL_USE).
        """
        try:
            chats = await DB.by_filters(
                model_name=AgentChats,
                where_clause={"session_id": session_id, "message_type": message_type.value},
                fetch_one=False,
                order_by="created_at",
            )
            if not chats:
                return []
            return [ReviewAgentChatDTO(**chat) for chat in chats]
        except Exception as ex:
            logger.error(
                f"Error occurred while fetching review agent chats for session_id: {session_id}, message_type: {message_type.value}, ex: {ex}"
            )
            raise ex

    @classmethod
    async def get_chats_by_agent_id_and_session(cls, session_id: int, agent_id: str) -> List[ReviewAgentChatDTO]:
        """
        Fetch chats by session_id and agent_id.
        """
        try:
            chats = await DB.by_filters(
                model_name=AgentChats,
                where_clause={"session_id": session_id, "agent_id": agent_id},
                fetch_one=False,
                order_by="created_at",
            )
            if not chats:
                return []
            return [ReviewAgentChatDTO(**chat) for chat in chats]
        except Exception as ex:
            logger.error(
                f"Error occurred while fetching review agent chats for session_id: {session_id}, agent_id: {agent_id}, ex: {ex}"
            )
            raise ex

    @classmethod
    async def db_insert(cls, chat_data: ReviewAgentChatCreateRequest) -> ReviewAgentChatDTO:
        """
        Insert a new review agent chat record.
        """
        try:
            payload = chat_data.model_dump(mode="json")
            row = await DB.insert_row(AgentChats, payload)
            row_dict = await row.to_dict()
            return ReviewAgentChatDTO(**row_dict)
        except Exception as ex:
            logger.error(f"Error inserting review agent chat: {chat_data.model_dump()}, ex: {ex}")
            raise ex

    @classmethod
    async def bulk_create_chats(cls, chats: List[ReviewAgentChatCreateRequest]) -> None:
        """
        Bulk create review agent chats in the database.

        Args:
            chats (List[ReviewAgentChatCreateRequest]): List of ReviewAgentChatCreateRequest objects to be created.
        """
        try:
            agent_chats = []
            for chat in chats:
                chat_dict = chat.model_dump()
                agent_chats.append(AgentChats(**chat_dict))
            await AgentChats.bulk_create(agent_chats)
        except Exception as ex:
            logger.error(f"Error bulk creating review agent chats, ex: {ex}")
            raise ex
