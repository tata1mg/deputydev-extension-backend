from enum import Enum

from pydantic import BaseModel


class Clients(Enum):
    CLI = "CLI"
    BACKEND = "BACKEND"
    VACODE_EXT = "VACODE_EXT"


class ClientData(BaseModel):
    client: Clients
    client_version: str
