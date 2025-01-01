import argparse
import asyncio
import logging
import os
import signal
import sys
import warnings
from concurrent.futures import ProcessPoolExecutor
from io import StringIO
from types import FrameType
from typing import Dict, List, Optional, Tuple, Type

from app.common.services.repo.local_repo.managers.git_repo import GitRepo
from app.main.blueprints.one_dev_cli.app.clients.one_dev import OneDevClient
from app.main.blueprints.one_dev_cli.app.constants.cli import CLIOperations
from app.main.blueprints.one_dev_cli.app.managers.features.dataclasses.main import (
    FeatureNextAction,
)
from app.main.blueprints.one_dev_cli.app.ui.helpers.feature_runner import FeatureRunner
from app.main.blueprints.one_dev_cli.app.ui.screens.authentication import Authentication
from app.main.blueprints.one_dev_cli.app.ui.screens.base_screen_handler import (
    BaseScreenHandler,
)
from app.main.blueprints.one_dev_cli.app.ui.screens.chat import ChatScreen
from app.main.blueprints.one_dev_cli.app.ui.screens.dataclasses.main import (
    AppContext,
    ScreenType,
)
from app.main.blueprints.one_dev_cli.app.ui.screens.exit import Exit
from app.main.blueprints.one_dev_cli.app.ui.screens.home import Home
from app.main.blueprints.one_dev_cli.app.ui.screens.query_selection import (
    QuerySelection,
)
from app.main.blueprints.one_dev_cli.app.ui.screens.repo_initialization import (
    InitializationScreen,
)
from app.main.blueprints.one_dev_cli.app.ui.screens.repo_selection import RepoSelection

os.environ["PYTHONWARNINGS"] = "ignore:resource_tracker:UserWarning"

log_stream = StringIO()
# Configure the root logger
logging.basicConfig(
    stream=log_stream,  # All logs go to this file
    level=logging.DEBUG,  # Capture all levels (DEBUG, INFO, WARNING, etc.)
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
warnings.filterwarnings("ignore")


cleanup_in_progress = False


def handle_keyboard_interrupt():
    global cleanup_in_progress
    if cleanup_in_progress:
        sys.exit(0)
    else:
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
    operation_group.add_argument("--jira-ticket", help="JIRA ticket ID")
    operation_group.add_argument(
        "--selected-text",
        help="The text selection to apply the operation on. Should be in the format file_path_relative_to_repo_root:start_line-end_line",
    )

    # PR and Diff options
    pr_group = parser.add_argument_group("PR and Diff Options")
    pr_group.add_argument("--apply-diff", action="store_true", help="Apply the diff to the codebase")
    pr_group.add_argument("--create-pr", action="store_true", help="Create a PR with the changes")
    pr_group.add_argument("--source-branch", help="Source branch for the PR")
    pr_group.add_argument("--destination-branch", help="Destination branch for the PR")
    pr_group.add_argument("--pr-title-prefix", help="Prefix for PR title")
    pr_group.add_argument("--commit-message-prefix", help="Prefix for commit message")

    # Authentication options
    auth_group = parser.add_argument_group("Authentication Options")
    auth_group.add_argument("--auth-token", help="Authentication token")

    # config options
    config_group = parser.add_argument_group("Config Options")
    config_group.add_argument("--debug", help="Path to the config file")


def validate_and_get_repo_id(repo: GitRepo, team_registered_repos: List[Dict[str, str]]) -> str:
    for team_repo in team_registered_repos:
        if team_repo["name"] == repo.get_repo_name() and team_repo["scm"] == repo.get_vcs_type():
            return team_repo["id"]
    raise ValueError(f"Repository {repo.get_repo_name()} not found in the team")


async def run_new_feature_session(
    app_context: AppContext,
) -> Tuple[AppContext, FeatureNextAction]:
    new_session_screens: List[Type[BaseScreenHandler]] = [
        Authentication,
        RepoSelection,
        InitializationScreen,
        QuerySelection,
    ]
    for screen in new_session_screens:
        app_context, redirect_screen = await screen(app_context).render()
        if redirect_screen == ScreenType.EXIT:
            return app_context, FeatureNextAction.ERROR_OUT_AND_END

    next_action, session_id = await FeatureRunner(app_context).run_feature()
    if session_id:
        app_context.session_id = session_id
    return app_context, next_action


async def render_home(app_context: AppContext) -> AppContext:

    app_context, redirect_after_home = await Home(app_context).render()
    if redirect_after_home == ScreenType.EXIT:
        return app_context

    redirect_screen: Optional[ScreenType] = None
    app_context, next_action = await run_new_feature_session(app_context)
    if next_action == FeatureNextAction.CONTINUE_CHAT:
        app_context, redirect_screen = await ChatScreen(app_context).render()

    if redirect_screen == ScreenType.HOME:
        await render_home(app_context)

    return app_context


async def main(process_executor: ProcessPoolExecutor):
    parser = argparse.ArgumentParser(description="OneDev CLI")
    init_args(parser)
    one_dev_client = OneDevClient()

    # get parsed user query
    args = parser.parse_args()

    async with AppContext(args=args, one_dev_client=one_dev_client, process_executor=process_executor) as app_context:
        try:
            redirect_screen: Optional[ScreenType] = None
            app_context, next_action = await run_new_feature_session(app_context)
            if next_action == FeatureNextAction.CONTINUE_CHAT:
                app_context, redirect_screen = await ChatScreen(app_context).render()

            if redirect_screen == ScreenType.HOME:
                app_context = await render_home(app_context)

            await Exit(app_context).render()
        except Exception as _ex:
            print(f"CLI encountered an unexpected error: {_ex}")
            print("Exiting ...")
        except KeyboardInterrupt:
            handle_keyboard_interrupt()


if __name__ == "__main__":
    with ProcessPoolExecutor(max_workers=1) as executor:
        asyncio.run(main(process_executor=executor))
