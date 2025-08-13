import json
from datetime import datetime
from typing import Any, Dict, Optional, Type

from app.main.blueprints.deputy_dev.services.code_review.vcs_review.pr_review_manager import (
    PRReviewManager,
)
from app.main.blueprints.deputy_dev.services.message_queue.subscribers.base.azure_bus_service_subscriber import (
    AzureBusServiceSubscriber,
)


class AzureBusServiceGenAiSubscriber(AzureBusServiceSubscriber):
    def get_queue_name(self) -> str:
        return self.config.get("AZURE_BUS_SERVICE", {}).get("SUBSCRIBE", {}).get("GENAI", {}).get("QUEUE_NAME", "")

    def get_queue_config(self) -> Dict[str, Any]:
        return self.config.get("AZURE_BUS_SERVICE", {}).get("SUBSCRIBE", {}).get("GENAI", {})

    @property
    def event_handler(self) -> Type[PRReviewManager]:
        return PRReviewManager

    # This can be removed and we can use publish function of base subscriber
    async def publish(
        self, payload: Dict[str, Any], attributes: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> None:
        session_id = f"{payload['vcs_type']}_{payload['pr_id']}_{payload['workspace_id']}_{payload['repo_name']}"
        message_id = f"{payload['vcs_type']}_{payload['pr_id']}_{payload['workspace_id']}_{payload['repo_name']}_{int(round(datetime.now().timestamp()))}"

        await self.init()
        payload = json.dumps(payload)
        try:
            await self.message_queue_manager.publish(
                payload=payload,
                attributes=attributes,
                batch=False,
                session_id=session_id,
                message_id=message_id,
                **kwargs,
            )
        finally:
            self.is_client_created = False
            await self.message_queue_manager.close()
