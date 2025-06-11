from typing import Optional
from app.backend_common.caches.base import Base


class CodeGenTasksCache(Base):
    """Redis cache for managing code generation task cancellation status and active queries by session_id"""
    _key_prefix = "codegen_session"
    _expire_in_sec = 3600  # 1 hour expiry for session data

    @classmethod
    async def is_session_cancelled(cls, session_id: int) -> bool:
        key = f"session:{session_id}:cancelled"
        result = await cls.get(key)
        return result == "true"

    @classmethod
    async def cancel_session(cls, session_id: int) -> None:
        key = f"session:{session_id}:cancelled"
        await cls.set(key, "true")

    @classmethod
    async def clear_session_cancellation(cls, session_id: int) -> None:
        key = f"session:{session_id}:cancelled"
        await cls.delete(key)

    @classmethod
    async def set_session_query(cls, session_id: int, query: str) -> None:
        key = f"session:{session_id}:query"
        await cls.set(key, query)

    @classmethod
    async def get_session_query(cls, session_id: int) -> Optional[str]:
        key = f"session:{session_id}:query"
        return await cls.get(key)

    @classmethod
    async def clear_session_query(cls, session_id: int) -> None:
        key = f"session:{session_id}:query"
        await cls.delete(key)

    @classmethod
    async def cleanup_session_data(cls, session_id: int) -> None:
        await cls.clear_session_cancellation(session_id)
        await cls.clear_session_query(session_id)

    @classmethod
    async def prepare_new_query_session(cls, session_id: int) -> None:
        key = f"session:{session_id}:cancelled"
        await cls.set(key, "false")
        
