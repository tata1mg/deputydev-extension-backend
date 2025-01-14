from app.backend_common.repository.db import DB
from app.main.blueprints.deputy_dev.models.dao.postgres.agent_comment_mappings import (
    AgentCommentMappings,
)


class AgentCommentMappingService:
    @classmethod
    async def bulk_insert(cls, mappings: list[AgentCommentMappings]):
        rows_inserted = await DB.bulk_create(AgentCommentMappings, mappings)
        return rows_inserted
