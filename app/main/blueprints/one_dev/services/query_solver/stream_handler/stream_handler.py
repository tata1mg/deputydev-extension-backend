import asyncio
from datetime import datetime
from typing import Any, AsyncIterator, Awaitable, Callable, Dict, List, Optional, Tuple

import redis.asyncio as redis
from pydantic import BaseModel

from app.backend_common.utils.redis_wrapper.client import BaseServiceCache


class StreamHandler(BaseServiceCache):
    """
    StreamHandler class for managing Redis streams with automatic expiration.

    This class provides functionality to:
    - Push BaseModel messages to Redis streams
    - Read BaseModel messages from Redis streams with offset support
    - Automatically expire streams after 10 minutes
    - Return functions that create async iterators for both existing and upcoming messages
    """

    _service_prefix: str = "stream_handler"
    _key_prefix: str = "stream"
    _delimiter: str = ":"

    # Stream TTL in seconds (10 minutes)
    STREAM_TTL = 600

    @classmethod
    def _get_stream_key(cls, stream_id: str) -> str:
        """Get the full Redis key for a stream."""
        return cls.prefixed_key(stream_id)

    @classmethod
    async def push_to_stream(cls, stream_id: str, data: BaseModel, message_id: str = "*") -> str:
        """
        Push a message to a Redis stream.

        Args:
            stream_id (str): The identifier for the stream
            data (BaseModel): The message data to push as a Pydantic BaseModel
            message_id (str): The message ID (defaults to '*' for auto-generated)

        Returns:
            str: The message ID that was assigned to the message
        """
        print("Pushing to stream:", stream_id, "Data:", data)
        stream_key = cls._get_stream_key(stream_id)

        # Serialize BaseModel to JSON string for Redis storage
        redis_data = {"data": data.model_dump_json()}

        # Push to stream using XADD
        result = await cls._redis_xadd(stream_key, redis_data, message_id)

        # Set expiration on the stream
        await cls._set_stream_expiration(stream_key)

        return result

    @classmethod
    def get_from_stream(
        cls,
        stream_id: str,
        offset_id: str = "0",
        count: Optional[int] = None,
        block_timeout: Optional[int] = 1000,
        model_class: Optional[type] = None,
    ) -> Callable[[], AsyncIterator[BaseModel]]:
        """
        Get messages from a Redis stream with offset support.
        Returns a function that returns an async iterator for both existing and upcoming messages.

        Args:
            stream_id (str): The identifier for the stream
            offset_id (str): The offset ID to start reading from (defaults to "0")
            count (Optional[int]): Maximum number of messages to read per batch
            block_timeout (Optional[int]): Timeout in milliseconds for blocking reads
            model_class (Optional[type]): Specific BaseModel class to deserialize to

        Returns:
            Callable[[], AsyncIterator[BaseModel]]: A function that returns an async iterator
        """
        print("Getting from stream:", stream_id, "Offset ID:", offset_id)

        async def stream_iterator() -> AsyncIterator[BaseModel]:
            """Async iterator function that yields BaseModel messages from the stream."""

            print("Starting stream iterator for:", stream_id, "from offset:", offset_id)
            stream_key = cls._get_stream_key(stream_id)
            current_offset = offset_id

            # First, read existing messages from the offset
            existing_messages: List[Tuple[str, List[Tuple[str, Dict[str, str]]]]] = await cls._redis_xread(
                {stream_key: current_offset}, count=count
            )

            for stream_name, messages in existing_messages:
                for message_id, fields in messages:
                    # Update current offset to the latest message ID
                    current_offset = message_id

                    # Parse and yield the BaseModel message
                    message_data: BaseModel = cls._parse_stream_message(message_id, fields, model_class)
                    print("Yielding existing message:", message_data)
                    yield message_data

            # Now start blocking reads for new messages
            # Use the last seen message ID for XREAD (don't use ">" as it's only for XREADGROUP)
            next_offset: str = current_offset

            while True:
                try:
                    # Check if stream still exists and hasn't expired
                    stream_exists: bool = await cls._stream_exists(stream_key)
                    print("Stream exists check for", stream_key, ":", stream_exists)
                    if not stream_exists:
                        print("Stream has expired or does not exist anymore:", stream_key)
                        break

                    # Blocking read for new messages
                    new_messages: List[Tuple[str, List[Tuple[str, Dict[str, str]]]]] = await cls._redis_xread(
                        {stream_key: next_offset}, count=count, block=block_timeout
                    )
                    print("New messages read from stream:", new_messages)

                    if not new_messages:
                        # Timeout occurred, continue to next iteration
                        continue

                    for stream_name, messages in new_messages:
                        for message_id, fields in messages:
                            # Update offset for next read
                            next_offset = message_id

                            # Parse and yield the BaseModel message
                            message_data: BaseModel = cls._parse_stream_message(message_id, fields, model_class)
                            print("Yielding new message:", message_data)
                            yield message_data

                except asyncio.CancelledError:
                    # Handle task cancellation gracefully
                    break
                except Exception as e:
                    # Log error and continue (could add proper logging here)
                    print(f"Error reading from stream {stream_id}: {e}")
                    await asyncio.sleep(1)  # Brief pause before retry

        return stream_iterator

    @classmethod
    def stream_from(
        cls,
        stream_id: str,
        offset_id: str = "0",
        count: Optional[int] = None,
        block_timeout: Optional[int] = 1000,
        model_class: Optional[type] = None,
    ) -> Callable[[], AsyncIterator[BaseModel]]:
        """
        Convenience method to directly get an async iterator from a stream.
        This is equivalent to calling get_from_stream(...) and then calling the returned function.

        Args:
            stream_id (str): The identifier for the stream
            offset_id (str): The offset ID to start reading from (defaults to "0")
            count (Optional[int]): Maximum number of messages to read per batch
            block_timeout (Optional[int]): Timeout in milliseconds for blocking reads
            model_class (Optional[type]): Specific BaseModel class to deserialize to

        Returns:
            AsyncIterator[BaseModel]: An async iterator that yields BaseModel messages
        """
        return cls.get_from_stream(stream_id, offset_id, count, block_timeout, model_class)

    @classmethod
    async def _redis_xadd(cls, stream_key: str, data: Dict[str, str], message_id: str = "*") -> str:
        """Execute XADD command on Redis."""
        # Flatten the data dictionary for Redis XADD command
        args: List[str] = []
        for key, value in data.items():
            args.extend([key, value])

        result = await cls._get_redis_client().execute_command("XADD", stream_key, message_id, *args)
        return result

    @classmethod
    async def _redis_xread(
        cls, streams: Dict[str, str], count: Optional[int] = None, block: Optional[int] = None
    ) -> List[Tuple[str, List[Tuple[str, Dict[str, str]]]]]:
        """Execute XREAD command on Redis."""
        args: List[str] = ["XREAD"]

        if count is not None:
            args.extend(["COUNT", str(count)])

        if block is not None:
            args.extend(["BLOCK", str(block)])

        args.append("STREAMS")

        # Add stream names and their offsets
        stream_names: List[str] = list(streams.keys())
        stream_offsets: List[str] = list(streams.values())

        args.extend(stream_names)
        args.extend(stream_offsets)

        result = await cls._get_redis_client().execute_command(*args)
        return result or []

    @classmethod
    async def _stream_exists(cls, stream_key: str) -> bool:
        """Check if a stream exists in Redis."""
        result = await cls._get_redis_client().exists(stream_key)
        return bool(result)

    @classmethod
    async def _set_stream_expiration(cls, stream_key: str) -> None:
        """Set expiration time for a stream."""
        await cls._get_redis_client().expire(stream_key, cls.STREAM_TTL)

    @classmethod
    def _parse_stream_message(
        cls, message_id: str, fields: Dict[str, str], model_class: Optional[type] = None
    ) -> BaseModel:
        """
        Parse a Redis stream message into a BaseModel.

        Args:
            message_id (str): The Redis message ID
            fields (Dict[str, str]): The message fields from Redis
            model_class (Optional[type]): Specific BaseModel class to deserialize to

        Returns:
            BaseModel: Parsed message as BaseModel instance
        """
        import json

        from pydantic import ValidationError

        # Get the JSON data from the fields
        json_data = fields.get("data", "{}")

        try:
            # Parse JSON back to dict
            data_dict = json.loads(json_data)

            # If specific model class is provided, try to deserialize to that class
            if model_class and issubclass(model_class, BaseModel):
                try:
                    return model_class(**data_dict)
                except ValidationError:
                    # Fall through to generic wrapper if specific class fails
                    pass

            # Create a generic BaseModel wrapper with the data
            class StreamMessage(BaseModel):
                message_id: str
                data: Dict[str, Any]
                stream_timestamp: datetime

            return StreamMessage(
                message_id=message_id, data=data_dict, stream_timestamp=cls._extract_timestamp_from_id(message_id)
            )

        except (json.JSONDecodeError, ValidationError) as e:
            # Fallback: create a model with raw data
            class StreamMessage(BaseModel):
                message_id: str
                data: Dict[str, Any]
                stream_timestamp: datetime
                error: str

            return StreamMessage(
                message_id=message_id,
                data={"raw_fields": fields},
                stream_timestamp=cls._extract_timestamp_from_id(message_id),
                error=str(e),
            )

    @classmethod
    def _extract_timestamp_from_id(cls, message_id: str) -> datetime:
        """
        Extract timestamp from Redis stream message ID.

        Args:
            message_id (str): Redis stream message ID (format: timestamp-sequence)

        Returns:
            datetime: The timestamp when the message was added
        """
        try:
            timestamp_part: str = message_id.split("-")[0]
            timestamp_ms: int = int(timestamp_part)
            return datetime.fromtimestamp(timestamp_ms / 1000)
        except (ValueError, IndexError):
            return datetime.now()

    @classmethod
    def _get_redis_client(cls) -> redis.Redis:
        """Get the underlying Redis client for executing commands."""
        from app.backend_common.utils.redis_wrapper.registry import cache_registry

        return cache_registry[cls._host]._redis

    @classmethod
    async def get_stream_info(cls, stream_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a stream (length, first/last message IDs, etc.).

        Args:
            stream_id (str): The identifier for the stream

        Returns:
            Optional[Dict[str, Any]]: Stream information or None if stream doesn't exist
        """
        stream_key = cls._get_stream_key(stream_id)

        try:
            result: List[Any] = await cls._get_redis_client().execute_command("XINFO", "STREAM", stream_key)

            # Parse the result into a more readable format
            info: Dict[str, Any] = {}
            for i in range(0, len(result), 2):
                key: str = result[i].decode() if isinstance(result[i], bytes) else result[i]
                value: Any = result[i + 1]
                if isinstance(value, bytes):
                    value = value.decode()
                info[key] = value

            return info
        except Exception:
            return None

    @classmethod
    async def delete_stream(cls, stream_id: str) -> bool:
        """
        Delete a stream completely.

        Args:
            stream_id (str): The identifier for the stream

        Returns:
            bool: True if stream was deleted, False if it didn't exist
        """
        stream_key: str = cls._get_stream_key(stream_id)
        result: int = await cls._get_redis_client().delete(stream_key)
        return bool(result)
