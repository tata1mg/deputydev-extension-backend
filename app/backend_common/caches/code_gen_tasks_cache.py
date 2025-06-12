import json
from typing import Optional, Dict, Any
from app.backend_common.caches.base import Base


class CodeGenTasksCache(Base):
    """Redis cache for managing code generation task cancellation status and active queries by session_id"""
    _key_prefix = "codegen_session"
    _expire_in_sec = 3600  # 1 hour expiry for session data

    @classmethod
    async def _get_session_data(cls, session_id: int) -> Dict[str, Any]:
        """Get all session data from a single Redis key"""
        key = f"session:{session_id}"
        data = await cls.get(key)
        if data:
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                return {}
        return {}

    @classmethod
    async def _set_session_data(cls, session_id: int, data: Dict[str, Any]) -> None:
        """Set all session data to a single Redis key"""
        key = f"session:{session_id}"
        await cls.set(key, json.dumps(data))

    @classmethod
    async def is_session_cancelled(cls, session_id: int) -> bool:
        data = await cls._get_session_data(session_id)
        return data.get("cancelled", False)

    @classmethod
    async def cancel_session(cls, session_id: int) -> None:
        data = await cls._get_session_data(session_id)
        data["cancelled"] = True
        await cls._set_session_data(session_id, data)

    @classmethod
    async def clear_session_cancellation(cls, session_id: int) -> None:
        data = await cls._get_session_data(session_id)
        data["cancelled"] = False
        await cls._set_session_data(session_id, data)


    @classmethod
    async def get_session_query_and_llm_model(cls, session_id: int) -> tuple[Optional[str], Optional[str]]:
        """Get both query and llm_model in a single Redis call"""
        data = await cls._get_session_data(session_id)
        return data.get("query"), data.get("llm_model")

    @classmethod
    async def cleanup_session_data(cls, session_id: int) -> None:
        key = f"session:{session_id}"
        await cls.delete(key)


        
