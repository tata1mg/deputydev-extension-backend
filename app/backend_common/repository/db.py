from datetime import datetime, timezone
from typing import Any, Dict, List, Type, Union, overload

from tortoise import Model

from app.backend_common.repository.db_wrapper import ORMWrapper


class DB(ORMWrapper):
    @classmethod
    async def insert_row(cls, model_name: Type[Model], payload: Dict[str, Any]) -> Model:
        payload["created_at"] = datetime.now().replace(tzinfo=timezone.utc)
        payload["updated_at"] = datetime.now().replace(tzinfo=timezone.utc)
        return await DB.create(model_name, payload)

    @overload
    @classmethod
    async def by_filters(
        cls,
        model_name: Model,
        where_clause: Dict[str, Any],
        limit: int | None = None,
        offset: int | None = None,
        order_by: Union[List[Dict[str, Any]], str, None] = None,
        fetch_one: bool = True,
        only: Union[list, str] = None,
    ) -> Dict[str, Any]: ...

    @overload
    @classmethod
    async def by_filters(
        cls,
        model_name: Model,
        where_clause: Dict[str, Any],
        limit: int | None = None,
        offset: int | None = None,
        order_by: Union[List[Dict[str, Any]], str, None] = None,
        fetch_one: bool = False,
        only: Union[List[str], str, None] = None,
    ) -> List[Dict[str, Any]]: ...

    @classmethod
    async def by_filters(
        cls,
        model_name: Model,
        where_clause: Dict[str, Any],
        limit: int | None = None,
        offset: int | None = None,
        order_by: Union[List[Dict[str, Any]], str, None] = None,
        fetch_one: bool = False,
        only: Union[List[str], str, None] = None,
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        results = await cls.get_by_filters(
            model_name,
            where_clause,
            limit=1 if fetch_one else limit,
            offset=offset,
            order_by=order_by,
            only=only,
        )
        results = [dict(result) for result in results] if results else []
        if results and fetch_one:
            return results[0]
        return results

    @classmethod
    async def count_by_filters(
        cls,
        model_name: Model,
        filters: Dict[str, Any],
        order_by: Union[List[Dict[str, Any]], str, None] = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> int:
        result = await cls.get_by_filters_count(
            model=model_name, filters=filters, order_by=order_by, limit=limit, offset=offset
        )
        return result

    @classmethod
    async def by_filters_in_batches(
        cls, model_name: Model, where_clause: Dict[str, Any], limit: int | None = None
    ) -> List[Dict[str, Any]]:
        batch_offset, results = 0, []
        limit = limit
        while True:
            rows = await cls.get_by_filters(
                model_name,
                where_clause,
                limit=limit,
                offset=batch_offset,
                order_by="id",
            )
            batch_offset += limit
            results.extend(rows)
            if len(rows) < limit:
                break
        results = [await result.to_dict() for result in results] if results else []
        return results

    @classmethod
    async def update_by_filters(
        cls,
        row: Any,
        model_name: Model,
        payload: Dict[str, Any],
        where_clause: Dict[str, Any] | None = None,
        update_fields: List[Dict[str, Any]] | None = None,
    ) -> None:
        if payload and isinstance(payload, dict):
            payload["updated_at"] = datetime.now().replace(tzinfo=timezone.utc)
        await cls.update_with_filters(row, model_name, payload, where_clause, update_fields)

    @classmethod
    async def execute_raw_sql(cls, query: str, connection: str = "default") -> None:
        """
        Executes a raw SQL script using the specified connection.

        :param query: contains raw sql query with multiple statements
        which have to be executed
        :param connection: connection on which raw sql will be run
        :return:
        """
        return await cls.raw_sql_script(query, connection)
