from abc import abstractmethod
from typing import Optional, Tuple

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer
from prompt_toolkit.document import Document
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.validation import ValidationError, Validator

from app.main.blueprints.one_dev_cli.app.ui.screens.dataclasses.main import AppContext


class AsyncValidator(Validator):
    @abstractmethod
    async def validation_core(self, input_text: str) -> None:
        raise NotImplementedError("validation_core method must be implemented in subclass")

    async def validate_async(self, document: Document) -> None:
        await self.validation_core(document.text)

    def validate(self, document: Document) -> None:
        # this will run validation_core synchronously on a separate thread
        import asyncio
        from concurrent.futures import ThreadPoolExecutor

        # Run validation_core in a separate thread since it's async
        with ThreadPoolExecutor() as executor:
            future = executor.submit(lambda: asyncio.run(self.validation_core(document.text)))
            try:
                future.result()  # Wait for and get the result, will raise any validation errors
            except ValidationError as e:
                raise e
            except Exception as e:
                raise ValidationError(str(e))


class TextValidator(AsyncValidator):
    async def validation_core(self, input_text: str) -> None:
        if not input_text:
            raise ValidationError(message="Input cannot be empty", cursor_position=len(input_text))


class DummyCompleter(Completer):
    def get_completions(self, document, complete_event):
        while False:
            yield


class OptionalValidator(AsyncValidator):
    def __init__(self, validator: AsyncValidator):
        self.validator = validator
        super().__init__()

    async def validation_core(self, input_text: str) -> None:
        if input_text:
            await self.validator.validation_core(input_text)


class BooleanValidator(AsyncValidator):
    async def validation_core(self, input_text: str) -> None:
        if input_text.lower() not in ["y", "n"]:
            raise ValidationError(message="Input must be y/n", cursor_position=len(input_text))


async def validate_existing_text_arg_or_get_input(
    session: PromptSession[str],
    arg_name: str,
    prompt_message: str,
    validator: AsyncValidator,
    app_context: AppContext,
    validate_while_typing: bool = True,
    force_input: bool = False,
    default: str = "",
    optional: bool = False,
    completer: Optional[Completer] = None,
) -> Tuple[str, bool]:
    final_value: Optional[str] = None
    is_existing_arg_valid = False

    _clear_existing_arg = False

    validator_to_use = validator
    if optional:
        validator_to_use = OptionalValidator(validator)

    # Check if the existing arg is valid, if so, use it
    if not force_input:
        try:
            arg_value = getattr(app_context.args, arg_name)
            if arg_value:
                await validator_to_use.validation_core(arg_value)
                final_value = arg_value
                is_existing_arg_valid = True
        except Exception:
            _clear_existing_arg = True
    else:
        _clear_existing_arg = True

    if _clear_existing_arg and hasattr(app_context.args, arg_name):
        setattr(app_context.args, arg_name, None)

    # If the existing arg is not valid, get the input from the user
    if not final_value:
        with patch_stdout():
            final_value = await session.prompt_async(
                prompt_message,
                validator=validator_to_use,
                validate_while_typing=validate_while_typing,
                default=default,
                completer=completer or DummyCompleter(),
            )
    return final_value, is_existing_arg_valid


async def validate_existing_boolean_arg_or_get_input(
    session: PromptSession[str],
    arg_name: str,
    prompt_message: str,
    app_context: AppContext,
    force_input: bool = False,
) -> Tuple[bool, bool]:
    final_value: Optional[bool] = None
    is_existing_arg_valid = False

    _clear_existing_arg = False

    # Check if the existing arg is valid, if so, use it
    if not force_input:
        try:
            arg_value = getattr(app_context.args, arg_name)
            if arg_value and isinstance(arg_value, bool):
                final_value = arg_value
                is_existing_arg_valid = True
        except Exception:
            _clear_existing_arg = True
    else:
        _clear_existing_arg = True

    if _clear_existing_arg and hasattr(app_context.args, arg_name):
        setattr(app_context.args, arg_name, None)

    # If the existing arg is not valid, get the input from the user
    if final_value is None:
        with patch_stdout():
            user_resp = await session.prompt_async(prompt_message, validator=BooleanValidator())
            final_value = user_resp.lower() == "y"

    return final_value, is_existing_arg_valid
