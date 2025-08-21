import logging

from elasticapm.traces import execution_context

from app.backend_common.utils.sanic_wrapper.constants.logging import FORMAT_VERSION, LogType
from app.backend_common.utils.sanic_wrapper.ctx import _task_ctx


def patch_log_record_factory(
    *,
    service_name: str,
    branch_name: str,
    current_tag: str,
    host: str,
    port: int | str,
) -> None:
    """Modifiy the log record factory.

    Add custom attributes to each log record uniformly.
    """

    old_factory = logging.getLogRecordFactory()

    def record_factory(*args, **kwargs):
        """New log record factory.

        |-----------------|--------------------------------------------------|
        | Attribute       | Description                                      |
        |-----------------|--------------------------------------------------|
        | version         | Log format version                               |
        | request_id      | Request ID from the task context                 |
        | logtype         | Log type based on logger                         |
        | service_name    | Name of the service                              |
        | branchname      | Branch name of the service                       |
        | current_tag     | Current tag of the service                       |
        | host            | Host and port of the service                     |
        | transaction_id  | Elastic APM transaction ID                       |
        | trace_id        | Elastic APM trace ID                             |
        | span_id         | Elastic APM span ID                              |
        |-----------------|--------------------------------------------------|

        """
        record = old_factory(*args, **kwargs)

        # log format version
        record.version = FORMAT_VERSION

        # inject req id
        record.request_id = _task_ctx.req_id

        # ------------------------------ define logtype ------------------------------ #

        logger_name = record.name
        if logger_name == "sanic.access":
            record.logtype = str(LogType.ACCESS_LOG)
        elif logger_name == "aiohttp.external":
            record.logtype = str(LogType.EXTERNAL_CALL_LOG)
        elif record.request_id is None or record.request_id == "-":
            record.logtype = str(LogType.BACKGROUND_CUSTOM_LOG)
        else:
            record.logtype = str(LogType.CUSTOM_LOG)

        # ------------------------- inject serice attributes ------------------------- #

        record.service_name = service_name
        record.branchname = branch_name
        record.current_tag = current_tag
        record.host = f"{host}:{port}"

        # --------------------- inject elasticapm correlation Ids -------------------- #

        transaction = execution_context.get_transaction()

        transaction_id = transaction.id if transaction else None
        record.transaction_id = transaction_id

        trace_id = None
        if transaction and transaction.trace_parent:
            trace_id = transaction.trace_parent.trace_id

        record.trace_id = trace_id

        span = execution_context.get_span()
        span_id = span.id if span else None
        record.span_id = span_id

        return record

    logging.setLogRecordFactory(record_factory)
