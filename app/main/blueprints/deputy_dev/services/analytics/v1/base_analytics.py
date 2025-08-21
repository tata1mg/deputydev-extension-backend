from abc import ABC
from typing import Any, Dict, List

from app.backend_common.constants.constants import Connections
from app.backend_common.repository.db import DB


class BaseAnalytics(ABC):
    def __init__(
        self,
        start_date: str,
        end_date: str,
        repo_ids: str = None,
        graph_type: str = None,
        interval_filter: str = None,
    ) -> None:
        self.start_date = start_date
        self.end_date = end_date
        self.repo_ids = repo_ids or ""
        self.interval_filter = interval_filter
        self.graph_type = graph_type

    async def get_analytics_data(self) -> List[Dict[str, Any]]:
        """
        Executes the SQL query and fetches raw analytics data.

        Returns:
            list[dict[str, Any]]: A list of dictionaries representing the query results.
        """

        query = self.format_query()
        data = await DB.raw_sql(query, connection=Connections.DEPUTY_DEV_REPLICA.value)
        return data

    def format_query(self) -> str:
        """
        Formats and returns the SQL query string for analytics data retrieval.
        This method must be implemented by subclasses to define their specific query logic.

        Returns:
            str: The formatted SQL query string.

        Raises:
            NotImplementedError: If the subclass does not implement this method.
        """
        raise NotImplementedError("Subclasses must implement format query method")
