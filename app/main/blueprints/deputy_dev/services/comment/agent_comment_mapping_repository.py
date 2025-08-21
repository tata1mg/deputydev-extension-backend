from app.backend_common.repository.db import DB
from app.main.blueprints.deputy_dev.models.dao.postgres.agent_comment_mappings import (
    AgentCommentMappings,
)


class AgentCommentMappingService:
    @classmethod
    async def bulk_insert(cls, mappings: list[AgentCommentMappings]) -> int:
        rows_inserted = await DB.bulk_create(AgentCommentMappings, mappings, ignore_conflicts=True)
        return rows_inserted
