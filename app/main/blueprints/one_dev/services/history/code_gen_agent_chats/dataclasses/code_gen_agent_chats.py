import datetime

from pydantic import BaseModel

from app.main.blueprints.one_dev.models.dto.agent_chats import ActorType, MessageData


class ChatElement(BaseModel):
    actor: ActorType
    message_data: MessageData
    timestamp: datetime.datetime
