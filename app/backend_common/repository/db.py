from datetime import datetime, timezone
from typing import Any, Dict, List, Union, overload

from tortoise_wrapper.wrappers.db_wrapper import ORMWrapper


class DB(ORMWrapper):
    @classmethod
    async def insert_row(cls, model_name, payload):
        payload["created_at"] = datetime.now().replace(tzinfo=timezone.utc)
        payload["updated_at"] = datetime.now().replace(tzinfo=timezone.utc)
        return await DB.create(model_name, payload)

    @overload
    @classmethod
    async def by_filters(
        cls,
        model_name,
        where_clause: dict,
        limit: int = None,
        offset: int = None,
        order_by: Union[list, str] = None,
        fetch_one: bool = True,
        only: Union[list, str] = None,
    ) -> Dict[str, Any]:
        ...

    @overload
    async def by_filters(
        cls,
        model_name,
        where_clause: dict,
        limit: int = None,
        offset: int = None,
        order_by: Union[list, str] = None,
        fetch_one: bool = False,
        only: Union[list, str] = None,
    ) -> List[Dict[str, Any]]:
        ...

    @classmethod
    async def by_filters(
        cls,
        model_name,
        where_clause: dict,
        limit: int = None,
        offset: int = None,
        order_by: Union[list, str] = None,
        fetch_one: bool = False,
        only: Union[list, str] = None,
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        results = await cls.get_by_filters(
            model_name,
            where_clause,
            limit=1 if fetch_one else limit,
            offset=offset,
            order_by=order_by,
            only=only,
        )
        results = [await result.to_dict() for result in results] if results else []
        if results and fetch_one:
            return results[0]
        return results

    @classmethod
    async def count_by_filters(cls, model_name, filters, order_by=None, limit=None, offset=None):
        result = await cls.get_by_filters_count(
            model=model_name, filters=filters, order_by=order_by, limit=limit, offset=offset
        )
        return result

    @classmethod
    async def by_filters_in_batches(cls, model_name, where_clause, limit=None):
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
    async def update_by_filters(cls, row, model_name, payload, where_clause=None, update_fields=None):
        if payload and isinstance(payload, dict):
            payload["updated_at"] = datetime.now().replace(tzinfo=timezone.utc)
        await cls.update_with_filters(row, model_name, payload, where_clause, update_fields)

    @classmethod
    async def execute_raw_sql(cls, query, connection="default"):
        """
        Executes a raw SQL script using the specified connection.

        :param query: contains raw sql query with multiple statements
        which have to be executed
        :param connection: connection on which raw sql will be run
        :return:
        """
        return await cls.raw_sql_script(query, connection)
