from abc import ABC, abstractmethod

from aiokafka import AIOKafkaConsumer
from sanic.log import logger
from ujson import loads

from app.backend_common.repository.failed_operations.repository import (
    FailedOperationsRepository,
)


class BaseKafkaSubscriber(ABC):
    def __init__(self, config, topic_name):
        self.config = config
        kafka_config = config.get("KAFKA", {})
        self.consumer = AIOKafkaConsumer(
            topic_name,
            bootstrap_servers=kafka_config.get("HOST"),
            group_id=kafka_config.get("GROUP_ID"),
            value_deserializer=lambda x: loads(x.decode("utf-8")),
        )

    async def consume(self):
        """Start consuming messages from Kafka."""
        try:
            await self.consumer.start()
            async for message in self.consumer:
                try:
                    await self._process_message(message)
                except Exception as e:
                    logger.error(f"Error processing message: {str(e)}")
                    dlq_payload = {"data": message.value, "type": message.value["event"]}
                    await FailedOperationsRepository.db_insert(dlq_payload)
        except Exception as e:
            logger.error(f"Kafka consumer error: {str(e)}")
        finally:
            await self.consumer.stop()

    @abstractmethod
    async def _process_message(self, message):
        """Abstract method to be implemented by subclasses for handling messages."""
        pass
