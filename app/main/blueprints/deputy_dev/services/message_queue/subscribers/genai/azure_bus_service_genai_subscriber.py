import json
from datetime import datetime

from app.main.blueprints.deputy_dev.services.code_review.pr_review_manager import (
    PRReviewManager,
)
from app.main.blueprints.deputy_dev.services.message_queue.subscribers.base.azure_bus_service_subscriber import (
    AzureBusServiceSubscriber,
)


class AzureBusServiceGenAiSubscriber(AzureBusServiceSubscriber):
    def get_queue_name(self):
        return self.config.get("AZURE_BUS_SERVICE", {}).get("SUBSCRIBE", {}).get("GENAI", {}).get("QUEUE_NAME", "")

    def get_queue_config(self):
        return self.config.get("AZURE_BUS_SERVICE", {}).get("SUBSCRIBE", {}).get("GENAI", {})

    @property
    def event_handler(self):
        return PRReviewManager

    # This can be removed and we can use publish function of base subscriber
    async def publish(self, payload: dict, attributes=None, **kwargs):
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
