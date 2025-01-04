import traceback
from typing import Any, Dict, Optional, Tuple

from prompt_toolkit import PromptSession, print_formatted_text
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.shortcuts import ProgressBar
from prompt_toolkit.shortcuts.progress_bar import formatters

from app.common.utils.app_logger import AppLogger
from app.main.blueprints.one_dev_cli.app.ui.screens.base_screen_handler import (
    BaseScreenHandler,
)
from app.main.blueprints.one_dev_cli.app.ui.screens.dataclasses.main import (
    AppContext,
    ScreenType,
)


class InitializationScreen(BaseScreenHandler):
    def __init__(self, app_context: AppContext) -> None:
        super().__init__(app_context)
        self.session: PromptSession[str] = PromptSession()
        self.usage_hash: Optional[str] = None

    @property
    def screen_type(self) -> ScreenType:
        return ScreenType.REPO_INITIALIZATION

    async def get_chunkable_files_and_commit_hashes(self, progressbar: ProgressBar):
        if self.app_context.local_repo is None:
            raise ValueError("Local repo not found in app context")
        self.app_context.chunkable_files_with_hashes = (
            await self.app_context.local_repo.get_chunkable_files_and_commit_hashes()
        )

    async def initialize_vector_db(self, progressbar: ProgressBar):
        if self.app_context.init_manager is None:
            raise ValueError("Init manager not found in app context")
        self.app_context.weaviate_client = await self.app_context.init_manager.initialize_vector_db(
            should_clean=self.app_context.args.clean_cache or False
        )

    async def fetch_embedding_manager(self, progressbar: ProgressBar):
        if self.app_context.init_manager is None:
            raise ValueError("Init manager not found in app context")
        self.app_context.embedding_manager = self.app_context.init_manager.embedding_manager

    async def prefill_vector_store(self, progressbar: ProgressBar):
        if self.app_context.init_manager is None:
            raise ValueError("Init manager not found in app context")
        if not self.app_context.chunkable_files_with_hashes:
            raise ValueError("Chunkable files and hashes should be pre-processed")
        usage_hash = await self.app_context.init_manager.prefill_vector_store(
            chunkable_files_and_hashes=self.app_context.chunkable_files_with_hashes, progressbar=progressbar
        )
        self.app_context.usage_hash = usage_hash

    async def render(self, **kwargs: Dict[str, Any]) -> Tuple[AppContext, ScreenType]:
        if self.app_context.local_repo is None:
            raise ValueError("Local repo not found in app context")

        if self.app_context.init_manager is None:
            raise ValueError("Init manager not found in app context")

        functions = [
            {
                "task_name": "Getting chunkable files and commit hashes",
                "task": self.get_chunkable_files_and_commit_hashes,
            },
            {
                "task_name": "Initializing vector db",
                "task": self.initialize_vector_db,
            },
            {
                "task_name": "Fetching embedding manager",
                "task": self.fetch_embedding_manager,
            },
            {
                "task_name": "Analyzing your code",
                "task": self.prefill_vector_store,
            },
        ]

        try:
            with patch_stdout():
                print_formatted_text("Initializing ...")
                print_formatted_text("The first-time setup may take a few minutes, please be patient.")
                with ProgressBar(
                    formatters=[
                        formatters.Label(),
                        formatters.Text(": [", style="class:percentage"),
                        formatters.Percentage(),
                        formatters.Text("]", style="class:percentage"),
                        formatters.Text(" "),
                        formatters.Bar(sym_a="#", sym_b="#", sym_c="."),
                        formatters.Text("  "),
                    ]
                ) as pb:
                    pb_obj = pb(functions, total=len(functions), label="Initializing repo ...", remove_when_done=True)
                    for function in pb_obj:
                        pb_obj.label = function["task_name"]
                        await function["task"](progressbar=pb)

        except Exception as e:
            print_formatted_text("Initialization failed ...")
            AppLogger.log_debug(traceback.format_exc())
            print_formatted_text(f"Error: {e}")
            return self.app_context, ScreenType.HOME
        return self.app_context, ScreenType.DEFAULT
