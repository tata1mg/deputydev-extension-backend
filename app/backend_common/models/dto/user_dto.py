from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class UserDTO(BaseModel):
    id: Optional[int] = None
    email: str
    name: str
    org_name: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
