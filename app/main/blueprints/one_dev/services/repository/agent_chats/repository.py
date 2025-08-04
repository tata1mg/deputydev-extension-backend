from typing import List, Optional

from sanic.log import logger

from app.backend_common.repository.db import DB
from app.main.blueprints.one_dev.models.dao.postgres.agent_chats import AgentChats
from app.main.blueprints.one_dev.models.dto.agent_chats import (
    AgentChatCreateRequest,
    AgentChatDTO,
    AgentChatUpdateRequest,
)


class AgentChatsRepository:
    @classmethod
    async def get_chats_by_session_id(cls, session_id: int) -> List[AgentChatDTO]:
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
            return [AgentChatDTO(**chat) for chat in chats]
        except Exception as ex:
            logger.error(f"Error occurred while fetching agent chats for session_id: {session_id}, ex: {ex}")
            raise ex

    @classmethod
    async def get_chat_by_id(cls, chat_id: int) -> Optional[AgentChatDTO]:
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
            return AgentChatDTO(**chat)
        except Exception as ex:
            logger.error(f"Error occurred while fetching agent chat by id: {chat_id}, ex: {ex}")
            raise ex

    @classmethod
    async def create_chat(cls, chat_data: AgentChatCreateRequest) -> AgentChatDTO:
        """
        Create a new chat entry.
        """
        try:
            payload = chat_data.model_dump(mode="json")
            created_chat = await DB.create(AgentChats, payload)
            return AgentChatDTO(**created_chat)
        except Exception as ex:
            logger.error(f"Error occurred while creating agent chat for session_id: {chat_data.session_id}, ex: {ex}")
            raise ex

    @classmethod
    async def update_chat(cls, chat_id: int, update_data: AgentChatUpdateRequest) -> Optional[AgentChatDTO]:
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
            logger.error(f"Error occurred while updating agent chat id: {chat_id}, ex: {ex}")
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
            logger.error(f"Error occurred while deleting agent chat id: {chat_id}, ex: {ex}")
            raise ex

    @classmethod
    async def get_latest_chats_by_session_id(cls, session_id: int, limit: int = 50) -> List[AgentChatDTO]:
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
            return [AgentChatDTO(**chat) for chat in chats]
        except Exception as ex:
            logger.error(f"Error occurred while fetching latest agent chats for session_id: {session_id}, ex: {ex}")
            raise ex

    @classmethod
    async def get_chats_by_actor_and_session(cls, session_id: int, actor: str) -> List[AgentChatDTO]:
        """
        Fetch chats by session_id and actor type (USER/ASSISTANT).
        """
        try:
            chats = await DB.by_filters(
                model_name=AgentChats,
                where_clause={"session_id": session_id, "actor": actor},
                fetch_one=False,
                order_by="created_at",
            )
            if not chats:
                return []
            return [AgentChatDTO(**chat) for chat in chats]
        except Exception as ex:
            logger.error(
                f"Error occurred while fetching agent chats for session_id: {session_id}, actor: {actor}, ex: {ex}"
            )
            raise ex

    @classmethod
    async def get_chats_by_message_type_and_session(cls, session_id: int, message_type: str) -> List[AgentChatDTO]:
        """
        Fetch chats by session_id and message type (TEXT/TOOL_USE/INFO).
        """
        try:
            chats = await DB.by_filters(
                model_name=AgentChats,
                where_clause={"session_id": session_id, "message_type": message_type},
                fetch_one=False,
                order_by="created_at",
            )
            if not chats:
                return []
            return [AgentChatDTO(**chat) for chat in chats]
        except Exception as ex:
            logger.error(
                f"Error occurred while fetching agent chats for session_id: {session_id}, message_type: {message_type}, ex: {ex}"
            )
            raise ex
