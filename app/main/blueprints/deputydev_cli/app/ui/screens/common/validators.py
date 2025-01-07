import asyncio
from abc import abstractmethod
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Tuple

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import CompleteEvent, Completer
from prompt_toolkit.document import Document
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.key_processor import KeyPressEvent
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.validation import ThreadedValidator, ValidationError, Validator

from app.main.blueprints.deputydev_cli.app.ui.screens.dataclasses.main import AppContext

thread_executor = ThreadPoolExecutor(max_workers=1)


class AsyncValidator(Validator):
    @abstractmethod
    async def validation_core(self, input_text: str) -> None:
        raise NotImplementedError("validation_core method must be implemented in subclass")

    async def validate_async(self, document: Document) -> None:
        await self.validation_core(document.text)

    def validate(self, document: Document) -> None:
        # Run validation_core in a separate thread since it's async
        # This allows us to bypass a core issue with prompt toolkit where
        # validation is sometimes done in async mode even if the program is
        # running in an event loop.

        # This class allows us to make validations completely async in Prompt Toolkit,
        # and makes use of future object to wait in a synchronous context without
        # freezing the main thread, which in turn makes the UI freeze.

        def run_async_validation():
            loop = None
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            loop.run_until_complete(self.validation_core(document.text))

        try:
            thread_executor.submit(run_async_validation).result()
        except ValidationError as e:
            raise e
        except Exception as e:
            raise ValidationError(message=str(e))


class TextValidator(AsyncValidator):
    async def validation_core(self, input_text: str) -> None:
        if not input_text:
            raise ValidationError(message="Input cannot be empty", cursor_position=len(input_text))


class DummyCompleter(Completer):
    def get_completions(self, document: Document, complete_event: CompleteEvent):
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
    only_complete_on_completer_selection: bool = False,
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
        key_bindings = None
        if completer and only_complete_on_completer_selection:
            key_bindings = KeyBindings()

            @key_bindings.add("enter")
            def _handle_enter(event: KeyPressEvent) -> None:
                """Custom behavior for the Enter key."""
                buffer = event.app.current_buffer
                if buffer.complete_state:
                    # If the completer is active, select the completion.
                    buffer.complete_state = None
                else:
                    # Otherwise, handle as a normal Enter key.
                    buffer.validate_and_handle()

        with patch_stdout():
            final_value = await session.prompt_async(
                prompt_message,
                validator=ThreadedValidator(validator_to_use),
                validate_while_typing=validate_while_typing,
                default=default,
                completer=completer or DummyCompleter(),
                key_bindings=key_bindings,
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
