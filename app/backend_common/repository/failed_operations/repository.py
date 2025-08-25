from typing import Any, Dict

from app.backend_common.models.dao.postgres.failed_operations import FailedOperations
from app.backend_common.repository.db import DB


class FailedOperationsRepository:
    @classmethod
    async def db_insert(cls, message: Dict[str, Any]) -> FailedOperations:
        row = await DB.insert_row(FailedOperations, message)
        return row
