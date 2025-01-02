from datetime import datetime
from typing import Union

from tortoise_wrapper.wrappers.db_wrapper import ORMWrapper


class DB(ORMWrapper):
    @classmethod
    async def insert_row(cls, model_name, payload):
        payload["created_at"] = datetime.now()
        payload["updated_at"] = datetime.now()
        return await DB.create(model_name, payload)

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
    ):
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
            payload["updated_at"] = datetime.now()
        await cls.update_with_filters(row, model_name, payload, where_clause, update_fields)
