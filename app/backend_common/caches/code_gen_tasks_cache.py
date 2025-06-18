import json
from typing import Optional, Dict, Any
from app.backend_common.caches.base import Base
import asyncio


class CodeGenTasksCache(Base):
    """Redis cache for managing code generation task cancellation status and active queries by session_id"""
    _key_prefix = "codegen_session"
    _expire_in_sec = 3600  

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
    async def set_session_data(cls, session_id: int, data: Dict[str, Any]) -> None:
        """Set all session data to a single Redis key"""
        key = f"session:{session_id}"
        data_curr = await cls._get_session_data(session_id)
        if data_curr is not None:
            data["cancelled"] = data.get("cancelled",data_curr.get("cancelled",False)) 
        await cls.set(key, json.dumps(data))

    @classmethod
    async def is_session_cancelled(cls, session_id: int) -> bool:
        data = await cls._get_session_data(session_id)
        return data.get("cancelled", False)

    @classmethod
    async def cancel_session(cls, session_id: int) -> None:
        data = await cls._get_session_data(session_id)
        data["cancelled"] = True
        await cls.set_session_data(session_id, data)


    @classmethod
    async def get_session_query_id(cls, session_id: int) -> Optional[int]:
        """Get the query_id for the session"""
        data = await cls._get_session_data(session_id)
        query_id = data.get("query_id")
        return int(query_id) if query_id is not None else None

    @classmethod
    async def set_session_query_id(cls, session_id: int, query_id: int) -> None:
        """Set the query_id for the session"""
        data = await cls._get_session_data(session_id)
        data["query_id"] = query_id
        await cls.set_session_data(session_id, data)

    @classmethod
    async def get_session_data_for_db(cls, session_id: int) -> tuple[Optional[str], Optional[str], Optional[int]]:
        """Get query, llm_model, and query_id in a single Redis call"""
        data = await cls._get_session_data(session_id)
        query_id = data.get("query_id")
        return data.get("query"), data.get("llm_model"), int(query_id) if query_id is not None else None

    @classmethod
    async def cleanup_session_data(cls, session_id: int) -> None:
        await asyncio.sleep(1.5)
        key = [f"session:{session_id}"]
        await cls.delete(key)


        
