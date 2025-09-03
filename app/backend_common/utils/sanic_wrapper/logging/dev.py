"""Developer friendly rich logging and tracebacks."""

import logging

from rich import traceback as rich_traceback
from rich.logging import RichHandler

from app.backend_common.utils.sanic_wrapper.constants.logging import TracebackTheme
from app.backend_common.utils.sanic_wrapper.utils import is_atty, is_local


def setup_rich_logging(
    show_locals: bool = True,
    traceback_theme: str | TracebackTheme = "one-dark",
):
    # SAFEGUARD
    if not is_local() or not is_atty():
        return

    if not isinstance(traceback_theme, TracebackTheme):
        theme = TracebackTheme(traceback_theme)

    # setup traceback formatting globally
    rich_traceback.install(
        show_locals=show_locals,
        width=None,  # no limit, this is mainly when server aborts abruptly
        locals_max_length=3,
        theme=theme.value,
    )

    # add rich traceback handler
    rich_handler = RichHandler(
        rich_tracebacks=True,
        show_time=True,
        omit_repeated_times=False,
        show_path=False,
        enable_link_path=True,
        tracebacks_show_locals=show_locals,
        locals_max_length=3,
        tracebacks_theme=traceback_theme,
    )

    for lname in ["sanic.root", "sanic.error", "sanic.server"]:
        logger = logging.getLogger(lname)

        for handler in logger.handlers:
            logger.removeHandler(handler)
        logger.addHandler(rich_handler)

    access_rich_handler = RichHandler(
        rich_tracebacks=True,
        show_time=True,
        omit_repeated_times=False,
        show_path=False,
        enable_link_path=True,
        tracebacks_show_locals=show_locals,
        locals_max_length=3,
        tracebacks_theme=traceback_theme,
    )
    access_fmt = logging.Formatter("%(method)s | %(host)s%(uri)s %(status_code)s  -  %(response_time)sms")
    access_rich_handler.setFormatter(access_fmt)

    access_logger = logging.getLogger("sanic.access")
    access_logger.handlers.clear()
    access_logger.addHandler(access_rich_handler)
