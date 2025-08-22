import json
from typing import List, Optional

from sanic.log import logger

from app.backend_common.repository.db import DB
from app.main.blueprints.one_dev.models.dao.postgres.query_summaries import (
    QuerySummaries,
)
from app.main.blueprints.one_dev.models.dto.query_summaries import (
    QuerySummaryData,
    QuerySummaryDTO,
)


class QuerySummarysRepository:
    @classmethod
    async def get_all_session_query_summaries(
        cls,
        session_id: int,
    ) -> List[QuerySummaryDTO]:
        try:
            query_summaries = await DB.by_filters(
                model_name=QuerySummaries,
                where_clause={"session_id": session_id},
            )
            if not query_summaries:
                return []
            return [QuerySummaryDTO(**query_summary) for query_summary in query_summaries]

        except Exception as ex:
            logger.error(
                f"error occurred while fetching message_threads from db for session_id filters : {session_id}, ex: {ex}"
            )
            raise ex

    @classmethod
    async def create_query_summary(cls, query_summary_data: QuerySummaryData) -> QuerySummaryDTO:
        try:
            message_sesison = await DB.create(QuerySummaries, query_summary_data.model_dump(mode="json"))
            return QuerySummaryDTO.model_validate_json(
                json_data=json.dumps(
                    dict(
                        id=message_sesison.id,
                        session_id=message_sesison.session_id,
                        query_id=message_sesison.query_id,
                        summary=message_sesison.summary,
                        created_at=message_sesison.created_at.isoformat(),
                        updated_at=message_sesison.updated_at.isoformat(),
                    )
                )
            )

        except Exception as ex:
            logger.error(
                f"error occurred while creating message_thread in db for message_thread_data : {query_summary_data}, ex: {ex}"
            )
            raise ex

    @classmethod
    async def get_query_summary(
        cls,
        session_id: int,
        query_id: str,
    ) -> Optional[QuerySummaryDTO]:
        try:
            query_summary = await DB.by_filters(
                model_name=QuerySummaries,
                where_clause={"session_id": session_id, "query_id": query_id},
                fetch_one=True,
            )
            if not query_summary:
                return None
            return QuerySummaryDTO(**query_summary)

        except Exception as ex:
            logger.error(
                f"error occurred while fetching message_threads from db for session_id filters : {session_id}, ex: {ex}"
            )
            raise ex

    @classmethod
    async def update_query_summary(cls, session_id: int, query_id: str, summary: str) -> None:
        try:
            await DB.update_by_filters(
                None, QuerySummaries, {"summary": summary}, {"session_id": session_id, "query_id": query_id}
            )
        except Exception as ex:
            logger.error(f"error occurred while updating query_summary in DB, ex: {ex}")
            raise ex
