from deputydev_core.utils.constants.enums import Clients
from pydantic import BaseModel


class ClientData(BaseModel):
    client: Clients
    client_version: str
