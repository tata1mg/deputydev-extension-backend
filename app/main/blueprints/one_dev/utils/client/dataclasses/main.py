from pydantic import BaseModel

from deputydev_core.utils.constants.enums import Clients


class ClientData(BaseModel):
    client: Clients
    client_version: str
