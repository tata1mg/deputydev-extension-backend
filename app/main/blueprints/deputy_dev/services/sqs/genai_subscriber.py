import json
from datetime import datetime

from app.common.services.sqs.base_subscriber import BaseSubscriber

from ..code_review.pr_review_manager import PRReviewManager


class GenaiSubscriber(BaseSubscriber):
    def get_queue_name(self):
        return self.config.get("SQS", {}).get("SUBSCRIBE", {}).get("GENAI", {}).get("QUEUE_NAME", "")

    def get_queue_config(self):
        return self.config.get("SQS", {}).get("SUBSCRIBE", {}).get("GENAI", {})

    @property
    def event_handler(self):
        return PRReviewManager

    async def publish(self, payload: dict, attributes=None, **kwargs):
        message_group_id = f"{payload['vcs_type']}_{payload['pr_id']}_{payload['workspace_id']}_{payload['repo_name']}"
        message_deduplication_id = f"{payload['vcs_type']}_{payload['pr_id']}_{payload['workspace_id']}_{payload['repo_name']}_{int(round(datetime.now().timestamp()))}"

        await self.init()
        payload = json.dumps(payload)
        try:
            await self.sqs_manager.publish_to_sqs(
                payload=payload,
                attributes=attributes,
                batch=False,
                message_group_id=message_group_id,
                message_deduplication_id=message_deduplication_id,
                **kwargs,
            )
        finally:
            self.is_client_created = False
            await self.sqs_manager.close()
