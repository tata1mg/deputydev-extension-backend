from enum import Enum
from typing import Annotated, Any, Dict, List, Literal, Union

from pydantic import BaseModel, Field


class UnifiedConversationRole(Enum):
    USER = "USER"
    ASSISTANT = "ASSISTANT"
    TOOL = "TOOL"


class UnifiedConversationTurnContentType(Enum):
    TEXT = "TEXT"
    IMAGE = "IMAGE"
    TOOL_REQUEST = "TOOL_REQUEST"
    TOOL_RESPONSE = "TOOL_RESPONSE"


class UnifiedTextConversationTurnContent(BaseModel):
    type: Literal[UnifiedConversationTurnContentType.TEXT] = UnifiedConversationTurnContentType.TEXT
    text: str


class UnifiedToolRequestConversationTurnContent(BaseModel):
    type: Literal[UnifiedConversationTurnContentType.TOOL_REQUEST] = UnifiedConversationTurnContentType.TOOL_REQUEST
    tool_use_id: str
    tool_name: str


class UnifiedToolResponseConversationTurnContent(BaseModel):
    type: Literal[UnifiedConversationTurnContentType.TOOL_RESPONSE] = UnifiedConversationTurnContentType.TOOL_RESPONSE
    tool_use_response: Dict[str, Any]


class UnifiedImageConversationTurnContent(BaseModel):
    type: Literal[UnifiedConversationTurnContentType.IMAGE] = UnifiedConversationTurnContentType.IMAGE
    base64_data: str
    image_mimetype: str


UnifiedConversationTurnContent = Annotated[
    Union[
        UnifiedTextConversationTurnContent,
        UnifiedImageConversationTurnContent,
        UnifiedToolRequestConversationTurnContent,
        UnifiedToolResponseConversationTurnContent,
    ],
    Field(discriminator="type"),
]


class UnifiedConversationTurn(BaseModel):
    role: UnifiedConversationRole
    content: List[UnifiedConversationTurnContent]
