"""Sanic signal handlers for Torpedo."""

import time

from rich import box
from rich.console import Console
from rich.table import Table
from sanic.log import access_logger
from sanic.response import HTTPResponse

from app.backend_common.utils.sanic_wrapper.constants.headers import USER_AGENT, X_SERVICE_NAME
from app.backend_common.utils.sanic_wrapper.request import Request


def rprint_headers(data: dict, title: str = "Dictionary"):
    """
    Prints a dictionary as a rich table.

    :param data: Dictionary to print
    :param title: Title of the table (optional)
    """
    console = Console()
    table = Table(
        box=box.SIMPLE,
        show_header=False,
        row_styles=["none", "dim"],
        width=80,
    )

    table.add_column("Key", style="bold bright_red", no_wrap=True)
    table.add_column("Value", style="white")

    for key, value in data.items():
        table.add_row("☵ " + str(key), "| " + str(value))

    console.print(table)


def log_request_info(request: Request, response: HTTPResponse):
    """Signal handler to log request info on response.

    |---------------------|-------------------------------------------------------------------------|
    | Field               | Description                                                             |
    |---------------------|-------------------------------------------------------------------------|
    | method              | The HTTP method of the request (e.g., GET, POST).                       |
    | uri                 | The URI path of the request.                                            |
    | content_type        | The content type of the request.                                        |
    | client.ip           | The IP address of the client making the request.                        |
    | client.service_name | The service name of the client, extracted from headers.                 |
    | client.user_agent   | The user agent of the client, extracted from headers.                   |
    | status_code         | The HTTP status code of the response.                                   |
    | headers             | The headers of the request (logged if verbosity > 0).                   |
    | query_params        | The query parameters of the request (logged if verbosity > 0).          |
    | body                | The body of the request (logged if verbosity > 1 and method is not GET).|
    | response_time       | The time taken to process the request, in milliseconds.                 |
    |---------------------|-------------------------------------------------------------------------|

    """  # noqa: E501

    req_info = {
        "method": request.method,
        "uri": request.path,
        "content_type": request.content_type,
        # client info
        "client.ip": request.ip,
        "client.service_name": request.headers.get(X_SERVICE_NAME),
        "client.user_agent": request.headers.get(USER_AGENT),
        # response status
        "status_code": response.status,
    }

    verbosity = request.app.config.get("ACCESS_LOG_VERBOSITY", 0)

    if verbosity > 0:
        req_info["headers"] = request.headers
        req_info["query_params"] = request.args

    if verbosity > 1 and request.method != "GET":
        try:
            req_info["body"] = request.json
        except Exception:
            req_info["body"] = "[FAILED TO PARSE]"

    # response time
    req_info["response_time"] = int(time.perf_counter() * 1000) - request.ctx.started_at

    access_logger.info("", extra=req_info)


def log_rich_request_info(request: Request, response: HTTPResponse):
    req_info = {
        "method": request.method,
        "uri": request.path,
        "content_type": request.content_type,
        # client info
        "client.ip": request.ip,
        "client.service_name": request.headers.get(X_SERVICE_NAME),
        "client.user_agent": request.headers.get(USER_AGENT),
        # response status
        "status_code": response.status,
    }

    # response time
    req_info["response_time"] = int(time.perf_counter() * 1000) - request.ctx.started_at

    access_logger.info("", extra=req_info)
    rprint_headers(dict(request.headers))
