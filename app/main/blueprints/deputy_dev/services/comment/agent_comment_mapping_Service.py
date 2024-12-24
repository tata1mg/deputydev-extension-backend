from app.main.blueprints.deputy_dev.models.dao.agent_comment_mappings import (
    AgentCommentMappings,
)
from app.main.blueprints.deputy_dev.services.db.db import DB


class AgentCommentMappingService:
    @classmethod
    async def bulk_insert(cls, mappings: list[AgentCommentMappings]):
        rows_inserted = await DB.bulk_create(AgentCommentMappings, mappings)
        return rows_inserted
