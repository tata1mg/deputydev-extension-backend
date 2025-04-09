from typing import Any, Optional

from app.main.blueprints.deputy_dev.models.dto.message_queue.base_queue_message import (
    BaseQueueMessage,
)


class SQSMessage(BaseQueueMessage):
    receipt_handle: Optional[str] = None
