"""
This module contains logic for patching the standard logging library,
patching Sanic's default access logging, and modifying the log record factory.

Authors:
- Prashant Mishra <prashant.mishra@1mg.com>
- Lakshay Bansal <lakshay.bansal@1mg.com>
"""

import logging
import typing as t

from .formatters import StructuredLoggingFormatter


def patch_standard_logging(
    formatter_cls: t.Type[logging.Formatter] = StructuredLoggingFormatter,
):
    """Patch standard logging library to ensure each handler always uses given formatter.

    Defaults to `StructuredLoggingFormatter` for structured logging in PRODUCTION.

    - Patches `logging.lastResort` handler to use `StructuredLoggingFormatter`.
    - Modifies `logging._addHandlerRef` to automatically apply `StructuredLoggingFormatter` to new handlers.
    - Patches `logging.Handler.setFormatter` to prevent overriding the formatter unless it's a `StructuredLoggingFormatter`.
    - Updates all existing handlers to use `StructuredLoggingFormatter`.

    To make sure whenever a new handler is created StructuredLoggingFormatter is attached to it as formatter,
    instead of patching the `logging.Handler.__init__` we have patched the the `logging._addHandlerRef` method
    because `logging._addHandlerRef` is always called when a new handler is instantiated
    and it's relatively easy to patch this method.

    Author:
        Prashant Mishra <prashant.mishra@1mg.com>

    """  # noqa: E501

    log_message_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Patch lastResort handler
    fmt = formatter_cls(log_message_format)
    logging.lastResort.setFormatter(fmt)

    # Patch `logging._addHandlerRef` method so new handler
    # is always created with given formatter
    def _add_handler_ref_patched(handler):
        from logging import _acquireLock, _handlerList, _releaseLock, _removeHandlerRef, weakref  # noqa # fmt: skip

        _acquireLock()
        try:
            fmt = formatter_cls(log_message_format)
            handler.setFormatter(fmt)
            _handlerList.append(weakref.ref(handler, _removeHandlerRef))
        finally:
            _releaseLock()

    logging._addHandlerRef = _add_handler_ref_patched

    # Patch the `logging.Handler.setFormatter` method to ignore the setFormat operation
    def _set_formatter_patched(self, fmt):
        if not isinstance(fmt, formatter_cls):
            return
        self.formatter = fmt

    logging.Handler.setFormatter = _set_formatter_patched

    # Finally update formatter in existing handlers
    for weak_ref_handler in logging._handlerList:
        handler = weak_ref_handler()
        fmt = formatter_cls(log_message_format)
        handler.setFormatter(fmt)
