from sanic.log import logger
from torpedo.exceptions import BadRequestException

from app.common.constants.error_messages import ErrorMessages


class Validator:
    @classmethod
    def mandatory_params(cls, **kwargs):
        for key, value in kwargs.items():
            if value is None:
                raise BadRequestException(ErrorMessages.FIELD_REQUIRED.value.format(key=key))

    @classmethod
    def param_type_check(cls, required_type, **kwargs):
        for key, value in kwargs.items():
            try:
                value = required_type(value)
            except Exception as e:
                logger.error(f"Exception in param Check: {e}".format(e))
                raise BadRequestException(
                    ErrorMessages.TYPE_CHECK.value.format(
                        required_type=required_type,
                        received_type=type(value).__name__,
                        key=key,
                    )
                )
            if not isinstance(value, required_type):
                raise BadRequestException(
                    ErrorMessages.TYPE_CHECK.value.format(
                        required_type=required_type,
                        received_type=type(value).__name__,
                        key=key,
                    )
                )

    @classmethod
    def param_in_check(cls, key, param, acceptable_values):
        if param not in acceptable_values:
            raise BadRequestException(
                ErrorMessages.IN_CHECK.value.format(acceptable_values=acceptable_values, param_value=param, key=key)
            )
