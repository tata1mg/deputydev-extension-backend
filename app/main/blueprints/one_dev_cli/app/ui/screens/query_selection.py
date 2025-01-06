import os
import pathlib
from typing import Any, Dict, List, Tuple

from prompt_toolkit import PromptSession, print_formatted_text
from prompt_toolkit.completion import CompleteEvent, Completer, Completion
from prompt_toolkit.document import Document
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.validation import ValidationError

from app.common.utils.config_manager import ConfigManager
from app.main.blueprints.one_dev_cli.app.constants.cli import CLIFeatures, CLIOperations
from app.main.blueprints.one_dev_cli.app.managers.features.dataclasses.main import (
    TextSnippet,
)
from app.main.blueprints.one_dev_cli.app.ui.screens.base_screen_handler import (
    BaseScreenHandler,
)
from app.main.blueprints.one_dev_cli.app.ui.screens.common.validators import (
    AsyncValidator,
    TextValidator,
    validate_existing_text_arg_or_get_input,
)
from app.main.blueprints.one_dev_cli.app.ui.screens.dataclasses.main import (
    AppContext,
    PlainTextQuery,
    QueryType,
    ScreenType,
    TextSelectionQuery,
)

INT_MIN = -2147483648


class OperationCompleter(Completer):
    def get_completions(self, document: Document, complete_event: CompleteEvent):
        all_enabled_operations: List[CLIOperations] = []
        for feature in ConfigManager.configs["ENABLED_FEATURES"]:
            try:
                all_enabled_operations.append(CLIOperations(feature))
            except Exception:
                pass

        for operation in all_enabled_operations:
            yield Completion(
                operation.value,
                start_position=INT_MIN,
            )


class FilePathCompleter(Completer):
    def __init__(self, app_context: AppContext) -> None:
        self.app_context = app_context
        super().__init__()

    def get_completions(self, document: Document, complete_event: CompleteEvent):
        if not self.app_context.local_repo:
            return

        text = document.text
        # if text is empty, show nothing
        if not text:
            return

        # if text is at least one character, show all file paths which start with the text
        abs_repo_path = self.app_context.local_repo.repo_path
        abs_file_path = os.path.join(abs_repo_path, text)

        current_yields = 0
        for root, _, files in os.walk(abs_repo_path):
            for file in files:
                abs_current_file_path = os.path.join(root, file)
                if abs_current_file_path.startswith(abs_file_path):
                    if current_yields >= 7:
                        return
                    yield Completion(
                        abs_current_file_path[len(abs_file_path) :],
                        start_position=0,
                    )
                    current_yields += 1


class OperationValidator(AsyncValidator):
    async def validation_core(self, input_text: str) -> None:
        try:
            input_enum = CLIOperations(input_text)
            if input_enum.value not in ConfigManager.configs["ENABLED_FEATURES"]:
                raise ValidationError(
                    message=f"Operation {input_enum.value} is not a valid operation",
                    cursor_position=len(input_text),
                )
        except Exception:
            raise ValidationError(message="Invalid operation", cursor_position=len(input_text))


class FileSelectionValidator(AsyncValidator):
    def __init__(self, app_context: AppContext) -> None:
        self.app_context = app_context
        super().__init__()

    async def validation_core(self, input_text: str) -> None:
        if not self.app_context.local_repo:
            raise ValidationError(message="Repo not selected. File validation cannot happen")
        abs_filepath = os.path.join(self.app_context.local_repo.repo_path, input_text)
        # check if file exists
        if not pathlib.Path(abs_filepath).exists():
            raise ValidationError(message="Path does not exist")

        # check if path is a file
        if not os.path.isfile(abs_filepath):
            raise ValidationError(message="Invalid file path")

        # try to open the file to check if it is readable
        try:
            with open(abs_filepath, "r", encoding="utf-8") as f:
                _ = f.readlines()
        except Exception:
            raise ValidationError(message="Unreadable file (UTF-8 encoding is required)")


class MultiFileSelectionValidator(AsyncValidator):
    def __init__(self, app_context: AppContext) -> None:
        self.app_context = app_context
        super().__init__()

    async def validation_core(self, input_text: str) -> None:
        if not input_text:
            return
        if "," in input_text:
            all_filepaths = input_text.split(",")
            for filepath in all_filepaths:
                await FileSelectionValidator(app_context=self.app_context).validation_core(input_text=filepath)
        else:
            await FileSelectionValidator(app_context=self.app_context).validation_core(input_text=input_text)


class TextSelectionValidator(AsyncValidator):
    def __init__(self, app_context: AppContext) -> None:
        self.app_context = app_context
        super().__init__()

    async def validation_core(self, input_text: str) -> None:
        if not input_text:
            raise ValidationError(message="Input cannot be empty", cursor_position=len(input_text))

        filepath: str
        end_line: int

        try:
            raw_filepath, lines = input_text.split(":")
            lines = lines.split("-")

            if (
                len(lines) != 2
                or not lines[0].isnumeric()
                or not lines[1].isnumeric()
                or int(lines[0]) > int(lines[1])
                or int(lines[0]) < 1
                or int(lines[1]) < 1
                or not raw_filepath
            ):
                raise ValidationError(message="Invalid text selection format. Please check line numbers and file path.")

            filepath = raw_filepath.strip()
            end_line = int(lines[1])

        except Exception:
            raise ValidationError(
                message="Invalid text selection format. Please enter in the format: file_path:start_line-end_line. Path must be relative to the repository root."
            )

        await FileSelectionValidator(app_context=self.app_context).validation_core(filepath)

        # check if file exists, is readable and has the lines
        try:
            abs_filepath = os.path.join(self.app_context.local_repo.repo_path, filepath)
            with open(abs_filepath, "r", encoding="utf-8") as f:
                lines = f.readlines()
                _ = lines[end_line - 1]
        except Exception:
            raise ValidationError(message="Invalid text selection. Please check line numbers and file path.")


class TextSelectionOrLimitedLengthFileSelectionValidator(AsyncValidator):
    def __init__(self, max_file_line_length: int, app_context: AppContext) -> None:
        super().__init__()
        self.max_file_line_length = max_file_line_length
        self.app_context = app_context

    async def validation_core(self, input_text: str) -> None:
        if not self.app_context.local_repo:
            raise ValidationError(message="Repo not selected. File validation cannot happen")
        if not input_text:
            raise ValidationError(message="Input cannot be empty", cursor_position=len(input_text))

        has_text_selection = ":" in input_text
        is_valid_file = False

        if (
            not has_text_selection
            and await FileSelectionValidator(app_context=self.app_context).validation_core(input_text) is None
        ):
            abs_filepath = os.path.join(self.app_context.local_repo.repo_path, input_text)
            try:
                with open(abs_filepath, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    if len(lines) > self.max_file_line_length:
                        raise ValidationError(
                            message=f"File length exceeds {self.max_file_line_length} lines. Please provide a text selection instead."
                        )

                is_valid_file = True
            except Exception:
                raise ValidationError(message="Invalid file path")

        if not is_valid_file:
            await TextSelectionValidator(app_context=self.app_context).validation_core(input_text)


class MultiTextSelectionValidator(AsyncValidator):
    def __init__(self, app_context: AppContext) -> None:
        self.app_context = app_context
        super().__init__()

    async def validation_core(self, input_text: str) -> None:
        if not input_text:
            return
        if "," in input_text:
            all_selections = input_text.split(",")
            for selection in all_selections:
                await TextSelectionValidator(app_context=self.app_context).validation_core(input_text=selection)
        else:
            await TextSelectionValidator(app_context=self.app_context).validation_core(input_text=input_text)


class QuerySelection(BaseScreenHandler):
    feature_query_map: Dict[CLIFeatures, QueryType] = {
        CLIFeatures.CODE_GENERATION: QueryType.PLAIN_TEXT,
        CLIFeatures.DOCS_GENERATION: QueryType.TEXT_SELECTION,
        CLIFeatures.TASK_PLANNER: QueryType.PLAIN_TEXT,
        CLIFeatures.TEST_GENERATION: QueryType.TEXT_SELECTION,
    }

    def __init__(self, app_context: AppContext) -> None:
        super().__init__(app_context)
        self.session: PromptSession[str] = PromptSession()

    @property
    def screen_type(self) -> ScreenType:
        return ScreenType.QUERY_SELECTION

    async def render(self, **kwargs: Dict[str, Any]) -> Tuple[AppContext, ScreenType]:
        print_formatted_text(
            FormattedText(
                [
                    ("#ffff00", "• CODE_GENERATION - "),
                    (
                        "#729fcf",
                        'You can explain desired functionality in natural language text along with files and code snippets you want to focus on. The AI "understands" your descriptions and generates contextually relevant code.\n',
                    ),
                ]
            )
        )
        print_formatted_text(
            FormattedText(
                [
                    ("#ffff00", "• DOCS_GENERATION - "),
                    (
                        "#729fcf",
                        "Provide your code (class, function or file) with a custom prompt to generate docstrings\n",
                    ),
                ]
            )
        )
        print_formatted_text(
            FormattedText(
                [
                    ("#ffff00", "• TASK_PLANNER - "),
                    (
                        "#729fcf",
                        "Not ready to code? Generate an execution plan to write code snippets in a structured manner\n",
                    ),
                ]
            )
        )
        print_formatted_text(
            FormattedText(
                [
                    ("#ffff00", "• TEST_GENERATION - "),
                    (
                        "#729fcf",
                        "Provide your code snippets and a custom prompt to generate tailored unit tests\n",
                    ),
                ]
            )
        )

        operation, _ = await validate_existing_text_arg_or_get_input(
            session=self.session,
            arg_name="operation",
            prompt_message="Enter the operation: ",
            validator=OperationValidator(),
            completer=OperationCompleter(),
            app_context=self.app_context,
        )

        self.app_context.operation = CLIFeatures(operation)

        query_type = self.feature_query_map.get(self.app_context.operation)

        if query_type == QueryType.PLAIN_TEXT:
            query, _ = await validate_existing_text_arg_or_get_input(
                session=self.session,
                arg_name="query",
                prompt_message="Enter your query: ",
                validator=TextValidator(),
                app_context=self.app_context,
            )
            focus_files, _ = await validate_existing_text_arg_or_get_input(
                session=self.session,
                arg_name="Focus_files",
                prompt_message="[OPTIONAL]Enter focus files [COMMA SEPARATED](filepath_relative_to_repo_root):",
                validator=MultiFileSelectionValidator(self.app_context),
                app_context=self.app_context,
                completer=FilePathCompleter(self.app_context),
            )

            focus_snippets, _ = await validate_existing_text_arg_or_get_input(
                session=self.session,
                arg_name="focus_snippets",
                prompt_message="[OPTIONAL]Enter focus snippets [COMMA SEPARATED](filepath_relative_to_repo_root:start_line-end_line):",
                validator=MultiTextSelectionValidator(self.app_context),
                app_context=self.app_context,
                completer=FilePathCompleter(self.app_context),
            )
            text_snippets: List[TextSnippet] = []
            if focus_snippets:
                all_snippets = focus_snippets.split(",")
                for snippet in all_snippets:
                    filepath, lines = snippet.split(":")
                    lines = lines.split("-")
                    text_snippets.append(
                        TextSnippet(
                            file_path=filepath,
                            start_line=int(lines[0]),
                            end_line=int(lines[1]),
                        )
                    )

            self.app_context.query = PlainTextQuery(
                text=query,
                focus_files=focus_files.split(",") if focus_files else [],
                focus_snippets=text_snippets,
            )
        else:
            text_selection, _ = await validate_existing_text_arg_or_get_input(
                session=self.session,
                arg_name="selected_text",
                prompt_message="File/Snippet to run operation on (filepath_relative_to_repo_root:start_line-end_line / filepath_relative_to_root): ",
                validator=TextSelectionOrLimitedLengthFileSelectionValidator(
                    app_context=self.app_context, max_file_line_length=200
                ),
                completer=FilePathCompleter(self.app_context),
                app_context=self.app_context,
            )
            query, _ = await validate_existing_text_arg_or_get_input(
                session=self.session,
                arg_name="query",
                prompt_message="[OPTIONAL]Custom instructions: ",
                validator=TextValidator(),
                app_context=self.app_context,
                optional=True,
            )
            filepath_and_lines = text_selection.split(":")
            if len(filepath_and_lines) == 1:
                filepath = filepath_and_lines[0]
                lines = None
            else:
                filepath, lines = filepath_and_lines
                lines = lines.split("-")
            self.app_context.query = TextSelectionQuery(
                file_path=filepath,
                start_line=int(lines[0]) if lines else None,
                end_line=int(lines[1]) if lines else None,
                custom_instructions=query,
            )

        return self.app_context, ScreenType.DEFAULT
