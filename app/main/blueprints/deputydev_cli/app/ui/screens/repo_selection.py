import os
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from prompt_toolkit import PromptSession, print_formatted_text
from prompt_toolkit.completion import (
    CompleteEvent,
    Completer,
    Completion,
    ThreadedCompleter,
)
from prompt_toolkit.document import Document
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.validation import ValidationError

from app.common.services.repo.local_repo.base_local_repo import BaseLocalRepo
from app.common.services.repo.local_repo.factory import LocalRepoFactory
from app.common.services.repo.local_repo.managers.git_repo import GitRepo
from app.main.blueprints.deputydev_cli.app.managers.features.dataclasses.main import (
    RegisteredRepo,
)
from app.main.blueprints.deputydev_cli.app.managers.initialization.main import (
    InitializationManager,
)
from app.main.blueprints.deputydev_cli.app.ui.screens.base_screen_handler import (
    BaseScreenHandler,
)
from app.main.blueprints.deputydev_cli.app.ui.screens.common.validators import (
    AsyncValidator,
    validate_existing_text_arg_or_get_input,
)
from app.main.blueprints.deputydev_cli.app.ui.screens.dataclasses.main import (
    AppContext,
    ScreenType,
)


class RepoPathCompleter(Completer):
    def get_completions(self, document: Document, complete_event: CompleteEvent):
        text = document.text
        # if text is empty, show nothing
        if not text:
            return

        # if text is at least one character, show all file paths which start with the text
        abs_repo_path = os.path.join(text)

        get_last_path_component = abs_repo_path.split("/")[-1]
        if get_last_path_component:
            abs_repo_path = abs_repo_path[: -len(get_last_path_component)]

        current_yields = 0
        for root, dirs, _ in os.walk(abs_repo_path, topdown=True):
            for dir in dirs:
                abs_current_file_path = os.path.join(root, dir)
                if abs_current_file_path.startswith(abs_repo_path + get_last_path_component):

                    if current_yields >= 7:
                        return
                    yield Completion(
                        abs_current_file_path[len(abs_repo_path) + len(get_last_path_component) :],
                        start_position=0,
                    )
                    current_yields += 1
            # prevent os.walk from going into subdirectories
            dirs[:] = []


class RepoPathValidator(AsyncValidator):
    def __init__(self, app_context: AppContext) -> None:
        self.app_context = app_context
        super().__init__()

    async def validation_core(self, input_text: str) -> None:
        if not input_text:
            raise ValidationError(
                message="Repository path cannot be empty",
                cursor_position=len(input_text),
            )

        # check if the path is a valid directory
        if not Path(input_text).is_dir():
            raise ValidationError(
                message="Invalid path. Please enter a valid directory path",
                cursor_position=len(input_text),
            )

        # try to initialize the repo
        try:
            init_manager = InitializationManager(
                input_text, auth_token=self.app_context.auth_token, process_executor=self.app_context.process_executor
            )
            init_manager.get_local_repo()
        except Exception:
            raise ValidationError(
                message=f"Repo is not initializable at : {input_text}",
                cursor_position=len(input_text),
            )


class BranchNameValidator(AsyncValidator):
    def __init__(self, local_repo: GitRepo) -> None:
        self.local_repo = local_repo
        super().__init__()

    async def validation_core(self, input_text: str) -> None:
        if not input_text:
            raise ValidationError(message="Branch name cannot be empty", cursor_position=len(input_text))

        # check if the branch exists
        if not self.local_repo.branch_exists(input_text):
            raise ValidationError(
                message=f"Branch {input_text} does not exist. Please create it before selecting",
                cursor_position=len(input_text),
            )


class RepoSelection(BaseScreenHandler):
    def __init__(self, app_context: AppContext) -> None:
        super().__init__(app_context)
        self.session: PromptSession[str] = PromptSession()

    @property
    def screen_type(self) -> ScreenType:
        return ScreenType.REPO_SELECTION

    async def render(self, **kwargs: Dict[str, Any]) -> Tuple[AppContext, ScreenType]:
        # check if current directory is git repo
        current_dir_repo: Optional[BaseLocalRepo] = None
        if not self.app_context.args.repo_path:
            try:
                current_dir_repo = LocalRepoFactory.get_local_repo(str(Path.cwd()))
            except Exception:
                pass
        repo_path, _is_existing_arg_valid = await validate_existing_text_arg_or_get_input(
            session=self.session,
            arg_name="repo_path",
            prompt_message="Enter the path to the repository: ",
            validator=RepoPathValidator(self.app_context),
            app_context=self.app_context,
            default=current_dir_repo.repo_path if current_dir_repo and isinstance(current_dir_repo, GitRepo) else "",
            completer=ThreadedCompleter(RepoPathCompleter()),
        )
        if self.app_context.init_manager:
            # repeat initialization
            if self.app_context.init_manager.repo_path != repo_path:
                self.app_context.init_manager = InitializationManager(
                    repo_path,
                    auth_token=self.app_context.auth_token,
                    process_executor=self.app_context.process_executor,
                    weaviate_client=self.app_context.init_manager.weaviate_client,
                )
        else:
            self.app_context.init_manager = InitializationManager(
                repo_path, auth_token=self.app_context.auth_token, process_executor=self.app_context.process_executor
            )
        self.app_context.local_repo = self.app_context.init_manager.get_local_repo()

        # if local repo is a git repo, get the branch to use
        if isinstance(self.app_context.local_repo, GitRepo):
            (branch_name, _is_existing_arg_valid,) = await validate_existing_text_arg_or_get_input(
                session=self.session,
                arg_name="working_branch",
                prompt_message="Branch to checkout and use: ",
                validator=BranchNameValidator(self.app_context.local_repo),
                app_context=self.app_context,
                default=self.app_context.local_repo.get_active_branch(),
            )
            self.app_context.local_repo.checkout_branch(branch_name)

            # check if repo is registered
            try:
                repo_details = await self.app_context.one_dev_client.get_registered_repo_details(
                    payload={
                        "repo_name": self.app_context.local_repo.get_repo_name(),
                        "vcs_type": self.app_context.local_repo.get_vcs_type(),
                    },
                    headers={"Authorization": f"Bearer {self.app_context.auth_token}"},
                )
                if repo_details.get("repo_id") and repo_details.get("repo_url"):
                    self.app_context.registered_repo_details = RegisteredRepo(
                        repo_id=repo_details["repo_id"],
                        repo_url=repo_details["repo_url"],
                    )
            except Exception:
                pass

        # print a summary of the selected repo and branch if applicable

        print_formatted_text(FormattedText([("#4e9a06", "Selected repository:")]))
        print_formatted_text(
            FormattedText(
                [
                    (
                        "#4e9a06",
                        f"Repository path: {self.app_context.local_repo.repo_path}",
                    )
                ]
            )
        )
        if isinstance(self.app_context.local_repo, GitRepo):
            print_formatted_text(
                FormattedText(
                    [
                        (
                            "#4e9a06",
                            f"Branch: {self.app_context.local_repo.get_active_branch()}",
                        )
                    ]
                )
            )
            print_formatted_text(FormattedText([("#4e9a06", "Repository type: Git")]))
            # if self.app_context.registered_repo_details:
            #     print_formatted_text(
            #         FormattedText(
            #             [
            #                 (
            #                     "#4e9a06",
            #                     f"Repository is registered with ID: {self.app_context.registered_repo_details.repo_id}",
            #                 )
            #             ]
            #         )
            #     )
            # else:
            #     print_formatted_text(FormattedText([("#c4a000", "Repository is not registered")]))
        else:
            print_formatted_text(FormattedText([("#4e9a06", "Repository type: Non-VCS")]))
            print_formatted_text(
                FormattedText(
                    [
                        (
                            "#c4a000",
                            "Some functionality may be limited (PR creation, etc.)",
                        )
                    ]
                )
            )

        return self.app_context, ScreenType.DEFAULT
