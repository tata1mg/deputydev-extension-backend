from torpedo import CONFIG

from app.backend_common.utils.types.types import CloudProviders

config = CONFIG.config


class MessageQueueHelper:
    cloud_provider = config.get("CLOUD_PROVIDER")
    queue_config_key = {
        CloudProviders.AZURE.value: "AZURE_BUS_SERVICE",
        CloudProviders.AWS.value: "SQS",
    }

    @classmethod
    def is_queue_enabled(cls, config, queue_type):
        key = cls.queue_config_key[cls.cloud_provider]
        config.get(key, {}).get("SUBSCRIBE", {}).get(queue_type, {}).get("ENABLED", False)
        return config
