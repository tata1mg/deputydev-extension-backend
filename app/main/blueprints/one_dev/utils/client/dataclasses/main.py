from enum import Enum

from pydantic import BaseModel


class Clients(Enum):
    CLI = "CLI"
    BACKEND = "BACKEND"
    VSCODE_EXT = "VSCODE_EXT"


class ClientData(BaseModel):
    client: Clients
    client_version: str
