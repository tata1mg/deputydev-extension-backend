from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from app.main.blueprints.deputy_dev.models.dto.message_queue.common_message_queue_models import (
    Attribute,
)


class BaseQueueMessage(BaseModel):
    body: Optional[dict] = None
    attributes: Optional[List[Attribute]] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)
