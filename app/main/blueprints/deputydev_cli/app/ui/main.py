import argparse
import asyncio
import logging
import signal
import sys
import traceback
import warnings
from concurrent.futures import ProcessPoolExecutor
from io import StringIO
from types import FrameType
from typing import List, Optional, Tuple, Type

from deputydev_core.utils.app_logger import AppLogger
from deputydev_core.utils.config_manager import ConfigManager

from app.main.blueprints.deputydev_cli.app.clients.one_dev_cli_client import (
    OneDevCliClient,
)
from app.main.blueprints.deputydev_cli.app.constants.cli import CLIOperations
from app.main.blueprints.deputydev_cli.app.managers.features.dataclasses.main import (
    FeatureNextAction,
)
from app.main.blueprints.deputydev_cli.app.ui import auth_token
from app.main.blueprints.deputydev_cli.app.ui.helpers.feature_runner import (
    FeatureRunner,
)
from app.main.blueprints.deputydev_cli.app.ui.screens.base_screen_handler import (
    BaseScreenHandler,
)
from app.main.blueprints.deputydev_cli.app.ui.screens.chat import ChatScreen
from app.main.blueprints.deputydev_cli.app.ui.screens.dataclasses.main import (
    AppContext,
    ScreenType,
)
from app.main.blueprints.deputydev_cli.app.ui.screens.exit import Exit
from app.main.blueprints.deputydev_cli.app.ui.screens.home import Home
from app.main.blueprints.deputydev_cli.app.ui.screens.query_selection import (
    QuerySelection,
)
from app.main.blueprints.deputydev_cli.app.ui.screens.repo_initialization import (
    InitializationScreen,
)
from app.main.blueprints.deputydev_cli.app.ui.screens.repo_selection import (
    RepoSelection,
)

# log_stream = StringIO()
# # Configure the root logger
# logging.basicConfig(
#     stream=log_stream,  # All logs go to this file
#     level=logging.DEBUG,  # Capture all levels (DEBUG, INFO, WARNING, etc.)
# )
warnings.filterwarnings("ignore")


cleanup_in_progress = False


def handle_keyboard_interrupt():
    global cleanup_in_progress
    if cleanup_in_progress:
        print("Second KeyboardInterrupt detected during cleanup. Force exiting.")
        sys.exit(0)
    else:
        print("KeyboardInterrupt detected. Starting cleanup.")
        cleanup_in_progress = True


def exit_signal_handler(sig: int, frame: Optional[FrameType] = None):
    handle_keyboard_interrupt()


signal.signal(signal.SIGINT, exit_signal_handler)


def init_args(parser: argparse.ArgumentParser):
    # Source options
    source_group = parser.add_argument_group("Source Options")
    source_group.add_argument("--repo-path", help="Path to the repository")
    source_group.add_argument("--focus-files", nargs="+", help="Files to focus on")
    source_group.add_argument("--focus-snippets", nargs="+", help="Custom snippets to focus on")
    source_group.add_argument("--working-branch", help="Branch to work on")

    # Operation-related arguments
    operation_group = parser.add_argument_group("Operation Options")
    operation_group.add_argument(
        "--operation",
        help=f"Operation to perform. Possible values: {', '.join(CLIOperations.__members__)}",
    )
    operation_group.add_argument("--query", help="Query from the user")
    operation_group.add_argument(
        "--selected-text",
        help="The text selection to apply the operation on. Should be in the format file_path_relative_to_repo_root:start_line-end_line [Only applicable to TEST_GENERATION and DOCS_GENERATION]",
    )

    # PR and Diff options
    pr_group = parser.add_argument_group("PR and Diff Options")
    pr_group.add_argument("--apply-diff", action="store_true", help="Apply the diff to the codebase")
    pr_group.add_argument("--create-pr", action="store_true", help="Create a PR with the changes")
    pr_group.add_argument("--source-branch", help="Source branch for the PR")
    pr_group.add_argument("--destination-branch", help="Destination branch for the PR")
    pr_group.add_argument("--pr-title-prefix", help="Prefix for PR title")
    pr_group.add_argument("--commit-message-prefix", help="Prefix for commit message")

    # config options
    config_group = parser.add_argument_group("Config Options")
    config_group.add_argument("--debug", help="Run in debug mode", action="store_true")
    config_group.add_argument(
        "--clean-cache",
        help="Clean the cache. Use this to clean up if its taking more storage on your system. This might slow down DeputyDev CLI's pr_review_initialization process",
        action="store_true",
    )


async def run_new_feature_session(
    app_context: AppContext,
) -> Tuple[AppContext, Optional[FeatureNextAction], Optional[ScreenType]]:
    new_session_screens: List[Type[BaseScreenHandler]] = [
        RepoSelection,
        InitializationScreen,
        QuerySelection,
    ]
    for screen in new_session_screens:
        app_context, redirect_screen = await screen(app_context).render()
        if redirect_screen == ScreenType.EXIT:
            return app_context, FeatureNextAction.ERROR_OUT_AND_END, None
        if redirect_screen == ScreenType.HOME:
            return app_context, None, ScreenType.HOME

    next_action, session_id = await FeatureRunner(app_context).run_feature()
    if session_id:
        app_context.session_id = session_id
    return app_context, next_action, None


async def render_home(app_context: AppContext) -> AppContext:

    app_context, redirect_after_home = await Home(app_context).render()
    if redirect_after_home == ScreenType.EXIT:
        return app_context

    redirect_screen: Optional[ScreenType] = None
    app_context, next_action, screen_redirect = await run_new_feature_session(app_context)
    if screen_redirect:
        redirect_screen = screen_redirect
    else:
        if next_action == FeatureNextAction.CONTINUE_CHAT:
            app_context, redirect_screen = await ChatScreen(app_context).render()

    if redirect_screen == ScreenType.HOME:
        await render_home(app_context)

    return app_context


async def main(process_executor: ProcessPoolExecutor):
    one_dev_client = OneDevCliClient(ConfigManager.configs["HOST_AND_TIMEOUT"])
    parser = argparse.ArgumentParser(description="DeputyDev CLI")
    init_args(parser)

    # get parsed user query
    args = parser.parse_args()

    if args.debug:
        AppLogger.set_logger_config(
            debug=True,
            stream=sys.stderr,
        )
    else:
        # suppress logging
        logging.basicConfig(
            stream=StringIO(),
            level=logging.DEBUG,
        )

    async with AppContext(
        args=args, one_dev_client=one_dev_client, auth_token=auth_token, process_executor=process_executor
    ) as app_context:
        try:
            redirect_screen: Optional[ScreenType] = None
            app_context, next_action, screen_redirect = await run_new_feature_session(app_context)

            if screen_redirect:
                redirect_screen = screen_redirect
            else:
                if next_action == FeatureNextAction.CONTINUE_CHAT:
                    app_context, redirect_screen = await ChatScreen(app_context).render()

            if redirect_screen == ScreenType.HOME:
                app_context = await render_home(app_context)

            await Exit(app_context).render()
        except Exception as _ex:
            print(f"CLI encountered an unexpected error: {_ex}")
            AppLogger.log_debug(traceback.format_exc())
            print("Exiting ...")
        except KeyboardInterrupt:
            handle_keyboard_interrupt()


def run_main():
    with ProcessPoolExecutor(max_workers=ConfigManager.configs["NUMBER_OF_WORKERS"]) as executor:
        asyncio.run(main(executor))


if __name__ == "__main__":
    run_main()
