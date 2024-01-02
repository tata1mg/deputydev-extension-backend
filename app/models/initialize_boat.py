from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Union


class InitializeBoatResponseModel(BaseModel):
    show_boat: bool
    boat_name: str
    boat_logo: str
    welcome_msg: str

