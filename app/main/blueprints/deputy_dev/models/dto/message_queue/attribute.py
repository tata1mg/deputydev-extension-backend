from pydantic import BaseModel, ConfigDict


class Attribute(BaseModel):
    name: str
    value: str
