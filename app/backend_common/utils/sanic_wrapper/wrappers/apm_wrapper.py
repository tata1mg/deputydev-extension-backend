import sys
from typing import Optional

import elasticapm
from elasticapm import get_client
from elasticapm.conf.constants import OUTCOME
from wrapt import decorator

TRANSACTION_TYPE = "consumer"


def apm_wrapper(*, transaction_name: Optional[str] = None, transaction_type: str = TRANSACTION_TYPE):
    """
    method to pass events to apm
    :param transaction_name: name under which transactions will be grouped
    :param transaction_type: type of transaction
    :return: None
    """

    @decorator
    async def wrapper(wrapped, instance, args, kwargs):  # pylint: disable=W0613
        elasticapm_client = get_client()
        elasticapm_client.begin_transaction(transaction_type)
        elasticapm.set_transaction_name(transaction_name or wrapped.__name__)
        elasticapm.label(**kwargs)

        try:
            response = await wrapped(*args, **kwargs)
            elasticapm.set_transaction_outcome(OUTCOME.SUCCESS)
        except Exception as exc:
            elasticapm_client.capture_exception(sys.exc_info())
            elasticapm.set_transaction_outcome(OUTCOME.FAILURE)
            raise exc
        finally:
            elasticapm_client.end_transaction()

        return response

    return wrapper
