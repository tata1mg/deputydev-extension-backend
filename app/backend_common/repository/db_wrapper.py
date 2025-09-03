from __future__ import annotations

# ---------------------------------------------------------------------------- #
# TODO: add type hints
# TODO: add usage examples in docstrings
# TODO: improve documentation, convert to google style doctrings
# ---------------------------------------------------------------------------- #
from contextvars import ContextVar
from typing import Type
from tortoise import Tortoise, timezone
from tortoise.contrib.postgres.functions import Random
from tortoise.models import Model

from app.backend_common.utils.tortoise_wrapper.constants import DEFAULT_LIMIT, DEFAULT_OFFSET
from app.backend_common.utils.tortoise_wrapper.exceptions import BadRequestException

user_context_ctx: ContextVar[dict] = ContextVar("__tortoise_user_context", default={})


class ORMWrapper:
    @classmethod
    async def get_by_filters(
        cls,
        model: Model,
        filters: dict,
        order_by: str | list[str] | None = None,
        limit: int = DEFAULT_LIMIT,
        offset: int = DEFAULT_OFFSET,
        only: str | list[str] | None = None,
    ):
        """
        :param model: database model class
        :param filters: where conditions for filter
        :param order_by: for ordering on queryset
        :: Pass string value 'random' to fetch rows randomly
        :param limit: limit queryset result
        :param offset: offset queryset results
        :param only: Fetch ONLY the specified fields to create a partial model
        :return: list of model objects returned by the where clause
        """
        queryset = model.filter(**filters)
        if order_by:
            if isinstance(order_by, str):
                if order_by == "random":
                    queryset = queryset.annotate(order=Random())
                    order_by = "order"
                order_by = [order_by]
            queryset = queryset.order_by(*order_by)
        if limit:
            queryset = queryset.limit(limit)

        if offset:
            queryset = queryset.offset(offset)
        if only:
            if isinstance(only, str):
                only = [only]
            queryset = queryset.only(*only)

        return await queryset

    @classmethod
    def add_audit_fields(cls, model: Model, payload: dict, update_fields: list = None) -> tuple:
        """
        Adds audit fields to the payload dictionary and updates the list of fields to
        be updated.

        This method checks if the model has fields like 'updated_on', 'updated_at',
        and 'updated_by'. If these fields are present and not already in the payload,
        it adds them with the current timestamp or the current user's email. It also
        updates the list of fields to be updated if provided.

        :param model: The database model class which contains the fields to be audited.
        :param payload: A dictionary containing the data to be updated in the model.
        :param update_fields: A list of fields that need to be updated. If not provided,
                              an empty list is used.
        :return: A tuple containing the updated payload and the list
                 of fields to be updated.
        """
        if not update_fields:
            update_fields = []

        if "updated_on" in model._meta.db_fields:
            if "updated_on" not in payload:
                payload.update({"updated_on": timezone.now()})
                if len(update_fields) > 0:
                    update_fields.append("updated_on")
        elif "updated_at" in model._meta.db_fields:
            if "updated_at" not in payload:
                payload.update({"updated_at": timezone.now()})
                if len(update_fields) > 0:
                    update_fields.append("updated_at")

        if "updated_by" in model._meta.db_fields:
            if not payload.keys() & {"updated_by"}:
                user_context = user_context_ctx.get()
                updated_by = user_context.get("email", "")
                payload.update({"updated_by": updated_by})
                if len(update_fields) > 0:
                    update_fields.append("updated_by")
        return payload, update_fields

    # FIXME: either seperate update given row from where clause
    # or rearrange args/kwargs (hint: use *, / seperator for args/lwargs)
    @classmethod
    async def update_with_filters(cls, row, model: Model, payload: dict, where_clause=None, update_fields=None):
        """
        :param row: database model instance which needs to be updated
        :param model: database model class on which filters and
        update will be applied.
        Please see diff between the two.
        :param payload: values which will be updated in the database.
        :param where_clause: conditions on which update will work.
        :param update_fields: fields to update in case of model object update
        :return: None. update doesn;t return any values
        """
        payload, update_fields = cls.add_audit_fields(model, payload, update_fields)

        if where_clause:
            await model.filter(**where_clause).update(**payload)
        else:
            for key, value in payload.items():
                setattr(row, key, value)
            await row.save(update_fields=update_fields)

    @classmethod
    async def row_wise_update_with_filters(
        cls, row, model: Model, payload: dict, where_clause=None, update_fields=None
    ):
        """
        Note: This function updates rows individually to keep an audit history when
        "where clause" is used to select specific data. This detailed tracking can slow
        things down if many rows are involved. For faster updates, you can choose
        to skip the audit and use a different function "update_with_filters".

        :param row: database model instance which needs to be updated
        :param model: database model class on which filters and
        update will be applied.
        Please see diff between the two.
        :param payload: values which will be updated in the database.
        :param where_clause: conditions on which update will work.
        :param update_fields: fields to update in case of model object update
        :return: None. update doesn't return any values
        """
        payload, update_fields = cls.add_audit_fields(model, payload, update_fields)

        if where_clause:
            rows = await model.filter(**where_clause)
            for model_row in rows:
                for key, value in payload.items():
                    setattr(model_row, key, value)
                await row.save(update_fields=update_fields)
        else:
            for key, value in payload.items():
                setattr(row, key, value)
            await row.save(update_fields=update_fields)

    @classmethod
    async def create(cls, model: Type[Model], payload):
        """
        :param model: db model
        :param payload: create payload
        :return: model instance
        """
        if "created_by" in model._meta.db_fields:
            if not payload.keys() & {"created_by"}:
                user_context = user_context_ctx.get()
                created_by = user_context.get("email", "")
                payload.update({"created_by": created_by})

        row = await model.create(**payload)
        return row

    @classmethod
    async def bulk_create(
        cls,
        model: Model,
        objects,
        batch_size=None,
        ignore_conflicts=False,
        update_fields=None,
        on_conflict=None,
        using_db=None,
    ):
        """
        :param model: db model
        :param objects: list of objects to be created
        :param on_conflict: On conflict index name
        :param update_fields: Update fields when conflicts
        :param ignore_conflicts: Ignore conflicts when inserting
        :param batch_size: How many objects are created in a single query
        :param using_db: Specific DB connection to use instead of default bound
        :return: model instance
        """
        if "created_by" in model._meta.db_fields:
            for payload_obj in objects:
                if payload_obj.created_by is None:
                    user_context = user_context_ctx.get()
                    created_by = user_context.get("email", "")
                    payload_obj.created_by = created_by

        row = await model.bulk_create(objects, batch_size, ignore_conflicts, update_fields, on_conflict, using_db)
        return row

    @classmethod
    async def get_or_create_object(cls, model: Model, payload, defaults=None):
        """
        :param model: database model class which needs to be get or created
        :param payload: values on which get or create will happen
        :param defaults: values on which will used to create the data which
        we do not
        want to include in filtering
        :return: model object and created - true/false
        """
        defaults = defaults or {}
        row, created = await model.get_or_create(defaults=defaults, **payload)
        return row, created

    @classmethod
    async def delete_with_filters(cls, row, model: Model, where_clause):
        """
        :param row: model object
        :param model: db model
        :param where_clause: where conditional
        :return: None
        """
        if where_clause:
            await model.filter(**where_clause).delete()
        else:
            await row.delete()

    @classmethod
    async def raw_sql(cls, query, connection="default", values=None):
        """
        :param query: contains raw sql query which have to be executed
        :param connection: connection on which raw sql will be run
        :return:
        """
        conn = Tortoise.get_connection(connection)
        result = await conn.execute_query_dict(query, values)
        return result

    @classmethod
    async def get_by_filters_count(cls, model: Model, filters, order_by=None, limit=None, offset=None):
        """
        :param model: database model class
        :param filters: where conditions for filter
        :param order_by: for ordering on queryset
        :param limit: limit queryset result
        :param offset: offset queryset results
        :return: list of model objects returned by the where clause
        """
        queryset = model.filter(**filters)
        if order_by:
            queryset = queryset.order_by(order_by)
        if limit:
            queryset = queryset.limit(limit)

        if offset:
            queryset = queryset.offset(offset)

        return await queryset.count()

    @classmethod
    async def get_values_by_filters(cls, model: Model, filters, columns):
        """
        :param model: model object
        :param filters: where conditions for filter
        :param columns: list of columns ['patient_id', 'prescription_id']
        """
        queryset = await model.filter(**filters).values(*columns)
        return queryset

    @classmethod
    async def annotate_by_filters(
        cls,
        model: Model,
        filters,
        column,
        function,
        group_by=None,
        order_by=None,
        values=None,
    ):
        """
        :param model: model object
        :param filters: where conditions for filter
        :param column: The column which need for annotate
        :param function: Max/Min/Count (max, count)
        :param order_by: for ordering on queryset
        :param group_by: for grouping on queryset
        :param values: list of columns ['patient_id', 'prescription_id']
        """
        if not values:
            values = []

        try:
            agg_col_name = function.__name__.lower()
        except (TypeError, ValueError, AttributeError) as ex:
            raise BadRequestException(f"Invalid function name: {function}") from ex

        values.append(agg_col_name)
        queryset = model.annotate(**{agg_col_name: function(column)}).filter(**filters).group_by(group_by)
        if order_by:
            queryset = queryset.order_by(order_by)
        queryset = await queryset.values(*values)
        return queryset

    @classmethod
    async def raw_sql_script(cls, query, connection="default"):
        """
        :param query: contains raw sql query with multiple statements
        which have to be executed
        :param connection: connection on which raw sql will be run
        :return:
        """
        conn = Tortoise.get_connection(connection)
        await conn.execute_script(query)
