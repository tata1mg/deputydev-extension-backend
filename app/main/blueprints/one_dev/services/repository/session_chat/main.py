from typing import Any, Dict, List, Union

from sanic.log import logger

from app.backend_common.repository.db import DB
from app.main.blueprints.one_dev.models.dao.postgres.session_chats import SessionChats
from app.main.blueprints.one_dev.models.dto.session_chat import SessionChatDTO


class SessionChatService:
    @classmethod
    async def db_get(
        cls, filters: Dict[str, Any], fetch_one: bool = False
    ) -> Union[List[SessionChatDTO], SessionChatDTO]:
        try:
            session_chats = await DB.by_filters(model_name=SessionChats, where_clause=filters, fetch_one=False)
            if session_chats and fetch_one:
                return SessionChatDTO(**session_chats[0])
            elif session_chats:
                return [SessionChatDTO(**session_chat) for session_chat in session_chats]
            raise ValueError("No session chats found for the given filters.")
        except Exception as ex:  # noqa: BLE001
            logger.error(
                "error occurred while fetching sessionchat details from db for sessionchat filters : {}, ex: {}".format(
                    filters, ex
                )
            )

    @classmethod
    async def db_create(cls, session_chat: SessionChatDTO) -> bool:
        try:
            payload = session_chat.model_dump(mode="json")
            del payload["id"]
            del payload["created_at"]
            del payload["updated_at"]
            await DB.create(model=SessionChats, payload=payload)
            return True
        except Exception as ex:  # noqa: BLE001
            logger.exception(
                "error occurred while creating sessionchat details in db for sessionchat : {}, ex: {}".format(
                    session_chat, ex
                )
            )
            return False
