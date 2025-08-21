from __future__ import annotations

import sanic
from elasticapm import Client
from elasticapm.contrib.sanic import ElasticAPM as SanicElasticAPM
from elasticapm.instrumentation.packages.base import AbstractInstrumentedModule
from sanic.log import logger

from app.backend_common.utils.sanic_wrapper.wrappers.apm_wrapper import apm_wrapper

APM_CLIENT: Client | None = None


def init_apm(app: sanic.Sanic, config: dict) -> None:
    # Disable log record factory, it creates a lot of noise
    # instead we use a custom less expensive implementation
    # to insert correlation ids.
    config["DISABLE_LOG_RECORD_FACTORY"] = True

    # Framework labels for sanic. This is done automatically
    # for Django/Flask, this can be removed once such feature is
    # implemented for sanic instumentation in the sdk.
    config["FRAMEWORK_NAME"] = "sanic"
    config["FRAMEWORK_VERSION"] = sanic.__version__

    global APM_CLIENT  # noqa: PLW0603
    APM_CLIENT = Client(config=config)

    # We set `skip_init_exception_handler` true to prevent sdk from
    # patching sanic's excpetion handler, this is crucial as
    # it overrides the handler and clears all the registered handlers.
    # This will hopefully get fixed in future, currently we manually capture
    # the exceptions to apm in our patched handler.
    SanicElasticAPM(
        app,
        client=APM_CLIENT,
        skip_init_exception_handler=True,
    )

    # finally init custom intrumentation.
    init_custom_instrumentation()


def init_custom_instrumentation():
    """Instruments all registered methods/functions."""
    for instrumentation_class in ExtendedInstrumentaion.get_instrumentation_classes():
        obj = instrumentation_class()
        obj.instrument()


class ExtendedInstrumentaion(AbstractInstrumentedModule):
    """A Base class to be extended to create custom instrumentation.

    All classes that require custom instrumentation should extend this class.

    It extends `AbstractInstrumentedModule` from elastic apm sdk.
    It additionally maitains a list of all the subclassed, this is used to
    actually initialise the instrumentation of the custom moduels.

    The `instrument_list` is a list of (module, method) pairs that will be
    instrumented.
    1. The module path and function name to be instrumented.
    2. The specific function within the module that will be instrumented.

    The first element of the tuple should be the full path to the module.
    The second element should be the name of the function within that module.

    Author:
        - Amit Chand <amit.chand@1mg.com>
    """

    __instrumentation_classes = []

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        ExtendedInstrumentaion.__instrumentation_classes.append(cls)

    @classmethod
    def get_instrumentation_classes(cls):
        return cls.__instrumentation_classes


class SQSConsumerInstrumentation(ExtendedInstrumentaion):
    """Instruments BaseSQSWrapper from `commonutils`.

    Attributes:
        name (str): A unique name for the module.
        instrument_list (list): A list of tuples representing methods to be instrumented.
            Each tuple in the list contains two elements:
            1. The module path and function name to be instrumented.
            2. The specific function within the module that will be instrumented.

    Author:
        Amit Chand <amit.chand@1mg.com>

    """  # noqa: E501

    name = "SQSConsumer"
    instrument_list = [
        (
            "commonutils.wrappers.aws.sqs.base_sqs_wrapper",
            "BaseSQSWrapper.handle_event",
        )
    ]

    def call_if_sampling(self, module, method, wrapped, instance, args, kwargs):
        class_name = None
        try:
            class_name = args[0].__class__.__name__
        except Exception as exc:
            logger.error(
                "Exception in SQSConsumerInstrumentation call_if_sampling, error = %s",
                exc,
                exc_info=True,
            )

        async def async_wrapper(*args, **kwargs):
            # Call apm_wrapper with the necessary arguments
            apm_decorator = apm_wrapper(transaction_name=class_name)
            # Apply the decorator to the wrapped function
            decorated_function = apm_decorator(wrapped)
            # Execute the decorated function
            return await decorated_function(*args, **kwargs)

        return async_wrapper(*args, **kwargs)
