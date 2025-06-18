from abc import ABC, abstractmethod

from aiokafka import AIOKafkaConsumer
from sanic.log import logger
from ujson import loads

from app.backend_common.repository.failed_operations.repository import (
    FailedOperationsRepository,
)


def safe_json_deserializer(x):
    try:
        return loads(x.decode("utf-8"))
    except Exception as e:
        logger.error(f"Failed to deserialize message: {str(e)}")
        return None


class BaseKafkaSubscriber(ABC):
    def __init__(self, config, topic_name):
        self.config = config
        self.topic_name = topic_name
        kafka_config = config.get("KAFKA", {})
        self.consumer = AIOKafkaConsumer(
            topic_name,
            bootstrap_servers=kafka_config.get("HOST"),
            group_id=kafka_config.get("GROUP_ID"),
            value_deserializer=safe_json_deserializer,
        )

    async def consume(self):
        """Start consuming messages from Kafka."""
        try:
            logger.info("Starting kafka consumer")
            await self.consumer.start()
            logger.info("Kafka consumer started")
            async for message in self.consumer:
                # Skip messages that failed to deserialize
                if message.value is None:
                    logger.error(
                        f"Skipping message at offset {message.offset} on topic {self.topic_name}: failed to deserialize"
                    )
                    continue
                try:
                    logger.info("kafka message", message.value)
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
        raise NotImplementedError()
