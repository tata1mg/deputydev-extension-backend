from pydantic import BaseModel


class ConversationRole(BaseModel):
    USER = "USER"
    SYSTEM = "SYSTEM"


class ConversationTurn(BaseModel):
    role: ConversationRole
