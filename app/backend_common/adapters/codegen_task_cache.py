from deputydev_core.llm_handler.interfaces.caches_interface import SessionCacheInterface

from app.backend_common.caches.code_gen_tasks_cache import CodeGenTasksCache


class CodeGenTasksCacheAdapter(SessionCacheInterface):
    def __init__(self, cache: CodeGenTasksCache) -> None:
        self.cache = cache

    async def set_session_query_id(self, session_id: int, query_id: int) -> None:
        await self.cache.set_session_query_id(session_id, query_id)

    async def is_session_cancelled(self, session_id: int) -> bool:
        return await self.cache.is_session_cancelled(session_id)

    async def cleanup_session_data(self, session_id: int) -> None:
        await self.cache.cleanup_session_data(session_id)
