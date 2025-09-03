from __future__ import annotations

import os
import socket
import typing as t

from sanic import Blueprint, Config, Request, Sanic
from sanic.blueprint_group import BlueprintGroup
from sanic.handlers import ErrorHandler
from sanic.http import Http
from sanic.signals import Event
from typing_extensions import final

from app.backend_common.utils.sanic_wrapper.blueprints import health_bp
from app.backend_common.utils.sanic_wrapper.common_utils import CONFIG
from app.backend_common.utils.sanic_wrapper.config import HostConfig, SanicConfig
from app.backend_common.utils.sanic_wrapper.constants import ENV
from app.backend_common.utils.sanic_wrapper.constants.errors import APP_NOT_INIT_ERR
from app.backend_common.utils.sanic_wrapper.constants.sanic import ListenerEvent, MiddlewareLocation
from app.backend_common.utils.sanic_wrapper.exceptions import StartupException
from app.backend_common.utils.sanic_wrapper.listeners.adam import get_openapi_json_file
from app.backend_common.utils.sanic_wrapper.listeners.integrations import setup_apm, setup_sentry
from app.backend_common.utils.sanic_wrapper.listeners.meta import add_service_started, log_meta
from app.backend_common.utils.sanic_wrapper.logging.dev import setup_rich_logging
from app.backend_common.utils.sanic_wrapper.logging.factory import patch_log_record_factory
from app.backend_common.utils.sanic_wrapper.logging.patch import patch_standard_logging
from app.backend_common.utils.sanic_wrapper.middlewares import add_start_time, task_ctx_factory
from app.backend_common.utils.sanic_wrapper.request import SanicRequest
from app.backend_common.utils.sanic_wrapper.signals import log_request_info, log_rich_request_info
from app.backend_common.utils.sanic_wrapper.types import (
    HandlerExceptionTuple,
    ListenerEventTuple,
    MiddlewaresTargetTuple,
    SignalHandlerTuple,
)
from app.backend_common.utils.sanic_wrapper.utils import is_atty, is_local


@final
class SanicWrapper:
    """Entrypoint for a Sanic application.

    It encapsulates the configuration, setup, and execution of a Sanic application.
    It provides a simple and intuitive way to create, configure, and run a Sanic
    application with various features such as blueprints, listeners, middlewares,
    and error handlers.

    Args:
        blueprints (BlueprintGroup):
            A group of blueprints to be registered with the application.
        listeners (list[ListenerEventTuple], optional):
            A list of listeners to be registered with the application. Defaults to None.
        middlewares (list[MiddlewaresTargetTuple], optional):
            A list of middlewares to be registered with the application. Defaults to None.
        handlers (list[HandlerExceptionTuple], optional):
            A list of error handlers to be registered with the application. Defaults to None.
        service_config (dict, optional):
            The configuration for the service. Defaults to None.
        default_config (Config, optional):
            The default configuration for the application. Defaults to None.
        request_cls (Type[Request], optional):
            The request class to use for the application. Defaults to SanicRequest.
        error_handler (ErrorHandler, optional):
            The error handler for the application. Defaults to None.

    Methods:
        run(app: Sanic) -> None:
            Runs the Sanic application with the configured settings.
        create_app() -> Sanic:
            Creates and returns a Sanic application instance with the configured settings.

    Example:
        ```python
        from app.backend_common.utils.sanic_wrapper import SanicWrapper

        middlewares = [(parse_response_headers, "request"), (append_headers, "response")]

        sanic_wrapper = SanicWrapper(blueprints=blueprints, middlewares=middlewares)
        app = sanic_wrapper.create_app()
        ```

    Example:
        ```python
        from app.backend_common.utils.sanic_wrapper import SanicWrapper

        middlewares = [(parse_response_headers, "request"), (append_headers, "response")]

        sanic_wrapper = SanicWrapper(blueprints=blueprints, middlewares=middlewares)
        app = sanic_wrapper.create_app()
        ```

    """  # noqa: E501

    _DEFAULT_BLUEPRINTS: list[Blueprint] = [health_bp]

    _DEFAULT_LISTENERS: list[ListenerEventTuple] = [
        (add_service_started, ListenerEvent.BEFORE_SERVER_START),
        (setup_sentry, ListenerEvent.BEFORE_SERVER_START),
        (setup_apm, ListenerEvent.BEFORE_SERVER_START),
        (get_openapi_json_file, ListenerEvent.AFTER_SERVER_START),
        (log_meta, ListenerEvent.AFTER_SERVER_START),
    ]

    _DEFAULT_MIDDLEWARES: list[MiddlewaresTargetTuple] = [
        (add_start_time, MiddlewareLocation.REQUEST, 1000),
        (task_ctx_factory, MiddlewareLocation.REQUEST, 999),
    ]

    _DEFAULT_HANDLERS: list[HandlerExceptionTuple] = []

    _DEFAULT_SIGNAL_HANDLERS: list[SignalHandlerTuple] = []

    def __init__(
        self,
        blueprints: BlueprintGroup,
        listeners: list[ListenerEventTuple] | None = None,
        middlewares: list[MiddlewaresTargetTuple] | None = None,
        handlers: list[HandlerExceptionTuple] | None = None,
        signal_handlers: list[SignalHandlerTuple] | None = None,
        *,
        service_config: t.Dict[str, t.Any] | None = None,
        default_config: Config | None = None,
        request_cls: t.Type[Request] = SanicRequest,
        error_handler: ErrorHandler | None = None,
    ) -> None:
        self._app: Sanic | None = None

        # Prepare the components to attach to the application
        self._blueprints = Blueprint.group(*self._DEFAULT_BLUEPRINTS, blueprints)
        self._listeners = self._DEFAULT_LISTENERS + (listeners or [])
        self._middlewares = self._DEFAULT_MIDDLEWARES + (middlewares or [])
        self._handlers = self._DEFAULT_HANDLERS + (handlers or [])
        self._signal_handlers = self._DEFAULT_SIGNAL_HANDLERS + (signal_handlers or [])

        # Prepare app configuration
        self._service_config = service_config or CONFIG.config
        self._host_config: HostConfig = HostConfig.from_dict(self._service_config)

        # Set custom classes for sanic application
        self._default_config = default_config or SanicConfig()
        self._request_cls = request_cls
        self._error_handler = error_handler if error_handler else None

    def run(self) -> None:
        """Serve the configured Sanic application."""
        if self._app is None:
            raise StartupException(APP_NOT_INIT_ERR)

        self.__render_wall()
        self._run_server(self._app)

    def create_app(self) -> Sanic:
        """Create a configured Sanic app with all components attached.

        Returns
            Sanic: The sanic app instance.

        """
        if self._app is None:
            self._app = self._get_app()
            self._configure_logging()
            self._register_listeners()
            self._register_middlewares()
            self._register_handlers()
            self._register_blueprints()
            self._register_signal_handlers()

        return self._app

    def _get_app(self) -> Sanic:
        """Initialise and conifgure a `Sanic` app instance.

        Configures the app with custom config object, request class
        and default error handler.

        Returns
            Sanic: The sanic app instance.

        """
        app = Sanic(
            name=self._host_config.NAME,
            config=self._default_config,
            request_class=self._request_cls,
            error_handler=self._error_handler,
        )
        # Update the app config with service config.
        # This allows felxibility to config sanic at service level
        # & also makes service config available application wide.
        app.update_config(self._service_config)

        app.ctx.host_config = self._host_config

        return app

    def _run_server(self, app: Sanic) -> None:
        run_params: dict[str, t.Any] = {
            "host": self._host_config.HOST,
            "port": self._host_config.PORT,
            "debug": self._host_config.DEBUG,
            # =-= disable sanic's access logger =-=
            "access_log": False,
        }

        # Determine the process mode based on the configuration
        if self._host_config.WORKERS == 1 and self._host_config.SINGLE_PROCESS:
            run_params["single_process"] = True
        else:
            run_params["workers"] = self._host_config.WORKERS

        app.run(**run_params)

    def _register_blueprints(self) -> None:
        self._app.blueprint(self._blueprints)

    def _register_listeners(self) -> None:
        """Register listeners to the application."""
        for listener_tuple in self._listeners:
            if len(listener_tuple) == 2:
                priority = 0
                listener, event = listener_tuple
            else:
                listener, event, priority = listener_tuple

            if isinstance(event, ListenerEvent):
                event = str(event)

            self._app.register_listener(listener, event, priority=priority)

    def _register_middlewares(self) -> None:
        """Register middlewares to the application."""
        for middleware_tuple in self._middlewares:
            if len(middleware_tuple) == 2:
                priority = 0
                middleware, attach_to = middleware_tuple
            else:
                middleware, attach_to, priority = middleware_tuple

            if isinstance(attach_to, MiddlewareLocation):
                attach_to = str(attach_to)

            self._app.register_middleware(middleware, attach_to, priority=priority)

    def _register_handlers(self) -> None:
        """Register custom exception handlers to the application."""
        for handler, exceptions in self._handlers:
            if not isinstance(exceptions, (tuple, list)):
                exceptions = (exceptions,)

            for exception in exceptions:
                self._app.error_handler.add(exception=exception, handler=handler)

    def _register_signal_handlers(self):
        """Register signal handlers."""
        for handler, event in self._signal_handlers:
            self._app.add_signal(handler, event)

    def __render_wall(self) -> None:
        pass

    def _configure_logging(self) -> None:
        """Configure application logging.

        Warning:
            DO NOT SIMPLIFY. KEPT EXPLICIT BY CHOICE.

        """
        # =-= disable sanic's access logger =-=
        Http.log_response = lambda *_, **__: ...

        # pick vcs info from env vars
        # this is assumed to be injected
        # during the CD pipeline
        branch_name = os.getenv(ENV.GIT_BRANCH)
        release_tag = os.getenv(ENV.RELEASE_TAG)

        if is_local():
            # preventing ``socket.gaierror`` locally
            host = "localhost"
        else:
            # this step is important, DO NOT replace with config host
            # here we want the ground truth
            # i.e. host value from the actual machine
            host = socket.gethostbyname(socket.gethostname())

        # again, we want actual set name
        # to be source of truth
        # not the config read value
        service_name = self._app.name

        show_locals = self._app.config.get("RICH_SHOW_LOCALS", True)
        traceback_theme = self._app.config.get("RICH_TRACEBACK_THEME", "one-dark")

        if not self._host_config.DEBUG:
            # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
            # =-             P R O D U C T I O N             -=
            # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

            # =-= enable custom access logging =-=
            if self._host_config.ACCESS_LOG:
                self._signal_handlers.append((log_request_info, Event.HTTP_LIFECYCLE_RESPONSE))

            # =-= enable strucured logging =-=
            patch_standard_logging()

            # =-= modify log record factory  =-=
            patch_log_record_factory(
                service_name=service_name,
                branch_name=branch_name,
                current_tag=release_tag,
                host=host,
                port=self._host_config.PORT,
            )

            # EXPERIMENTAL
            if is_local() and is_atty() and self._host_config.DEV_MODE:
                setup_rich_logging(show_locals, traceback_theme)

        else:  # noqa: PLR5501
            # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
            # =-                  D E B U G                  -=
            # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

            patch_log_record_factory(
                service_name=service_name,
                branch_name=branch_name,
                current_tag=release_tag,
                host=host,
                port=self._host_config.PORT,
            )

            if is_local() and is_atty() and self._host_config.DEV_MODE:
                setup_rich_logging(show_locals, traceback_theme)

            if self._host_config.ACCESS_LOG:
                self._signal_handlers.append((log_rich_request_info, Event.HTTP_LIFECYCLE_RESPONSE))
