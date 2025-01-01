from enum import Enum

from pydantic import BaseModel

from app.main.blueprints.one_dev.utils.dataclasses.main import AuthData


class CodeGenIterativeHandlers(Enum):
    DIFF_CREATION = "DIFF_CREATION"
    CHAT = "CHAT"


class BaseCodeGenIterativeHandlerPayload(BaseModel):
    session_id: str
    auth_data: AuthData
