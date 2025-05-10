from typing import Any, Tuple

from deputydev_core.services.repo.local_repo.managers.git_repo_service import GitRepo
from prompt_toolkit import PromptSession, print_formatted_text
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.validation import ValidationError

from app.main.blueprints.deputydev_cli.app.managers.features.dataclasses.main import (
    PRConfig,
)
from app.main.blueprints.deputydev_cli.app.ui.screens.base_screen_handler import (
    BaseScreenHandler,
)
from app.main.blueprints.deputydev_cli.app.ui.screens.common.validators import (
    AsyncValidator,
    TextValidator,
    validate_existing_boolean_arg_or_get_input,
    validate_existing_text_arg_or_get_input,
)
from app.main.blueprints.deputydev_cli.app.ui.screens.dataclasses.main import (
    AppContext,
    ScreenType,
)


class DestinationBranchValidator(AsyncValidator):
    def __init__(self, app_context: AppContext) -> None:
        self.app_context = app_context
        super().__init__()

    async def validation_core(self, input_text: str) -> None:
        if not input_text:
            raise ValidationError(message="Branch cannot be empty")

        if not isinstance(self.app_context.local_repo, GitRepo) or not self.app_context.registered_repo_details:
            raise ValueError("Local repo should be a git repo for PR creation")

        if not self.app_context.local_repo.is_branch_available_on_remote(
            input_text, self.app_context.registered_repo_details.repo_url
        ):
            raise ValidationError(message=f"Branch {input_text} should exist on remote repository")


class PRConfigSelection(BaseScreenHandler):
    def __init__(self, app_context: AppContext) -> None:
        super().__init__(app_context)
        self.session: PromptSession[str] = PromptSession()

    @property
    def screen_type(self) -> ScreenType:
        return ScreenType.PR_CONFIG_SELECTION

    async def handle_local_changes(self):
        if not isinstance(self.app_context.local_repo, GitRepo) or not self.app_context.registered_repo_details:
            raise ValueError("Local repo should be a git repo for PR creation")
        if await self.app_context.local_repo.get_modified_or_renamed_files():
            print_formatted_text("Local changes found...")
            print_formatted_text(
                "You'll need to commit and push your local changes first. Please confirm the branch and commit message for this..."
            )

            (
                branch_name,
                _is_existing_arg_valid,
            ) = await validate_existing_text_arg_or_get_input(
                session=self.session,
                arg_name="working_branch",
                prompt_message="Branch (This will be used for further steps): ",
                validator=TextValidator(),
                app_context=self.app_context,
                default=self.app_context.local_repo.get_active_branch(),
                force_input=True,
            )

            commit_message_for_existing_changes: str
            with patch_stdout():
                commit_message_for_existing_changes = await self.session.prompt_async(
                    "Enter commit message for existing changes: ",
                    validator=TextValidator(),
                )

            self.app_context.local_repo.stage_changes()
            self.app_context.local_repo.checkout_branch(branch_name)

            self.app_context.local_repo.commit_changes(commit_message=commit_message_for_existing_changes)
            await self.app_context.local_repo.push_to_remote(
                branch_name=self.app_context.local_repo.get_active_branch(),
                remote_repo_url=self.app_context.registered_repo_details.repo_url,
            )
            print_formatted_text("Local changes committed and pushed successfully...")

    async def render(self, **kwargs: Any) -> Tuple[AppContext, ScreenType]:
        if self.app_context.registered_repo_details is None:
            print_formatted_text("PR creation is only supported for registered repos.")
            return self.app_context, ScreenType.DEFAULT

        pr_to_be_created = kwargs.get("pr_to_be_created", None)

        if pr_to_be_created is None:
            pr_to_be_created, _ = await validate_existing_boolean_arg_or_get_input(
                session=self.session,
                arg_name="create_pr",
                prompt_message="Do you want to create a PR? (Y/N): ",
                app_context=self.app_context,
            )

        if not pr_to_be_created:
            print_formatted_text("Skipping PR creation ...")
            return self.app_context, ScreenType.DEFAULT

        # check if local changes need to be committed and pushed before creating PR
        try:
            await self.handle_local_changes()
        except Exception as _ex:
            print_formatted_text(
                f"Error while handling local changes: {_ex}. PR cannot be created. Falling back to diff application..."
            )
            return self.app_context, ScreenType.DEFAULT

        source_branch, _ = await validate_existing_text_arg_or_get_input(
            session=self.session,
            arg_name="source_branch",
            prompt_message="Enter the source branch name: ",
            app_context=self.app_context,
            validator=TextValidator(),
        )

        destination_branch, _ = await validate_existing_text_arg_or_get_input(
            session=self.session,
            arg_name="destination_branch",
            prompt_message="Enter the target branch name: ",
            app_context=self.app_context,
            validator=DestinationBranchValidator(self.app_context),
        )

        pr_title_prefix, _ = await validate_existing_text_arg_or_get_input(
            session=self.session,
            arg_name="pr_title_prefix",
            prompt_message="Enter the PR title prefix: (Leave blank to skip)",
            app_context=self.app_context,
            validator=TextValidator(),
            optional=True,
        )

        commit_message_prefix, _ = await validate_existing_text_arg_or_get_input(
            session=self.session,
            arg_name="commit_message_prefix",
            prompt_message="Enter the commit message prefix: (Leave blank to skip)",
            app_context=self.app_context,
            validator=TextValidator(),
            optional=True,
        )

        self.app_context.pr_config = PRConfig(
            source_branch=source_branch,
            destination_branch=destination_branch,
            pr_title_prefix=pr_title_prefix,
            commit_message_prefix=commit_message_prefix,
        )

        return self.app_context, ScreenType.DEFAULT
