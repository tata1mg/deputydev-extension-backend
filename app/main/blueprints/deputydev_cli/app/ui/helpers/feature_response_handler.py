from typing import Union

from deputydev_core.services.repo.local_repo.managers.git_repo_service import GitRepo
from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import FormattedText

from app.main.blueprints.deputydev_cli.app.constants.cli import CLIFeatures
from app.main.blueprints.deputydev_cli.app.managers.features.dataclasses.main import (
    FinalFailedJob,
    FinalSuccessJob,
)
from app.main.blueprints.deputydev_cli.app.ui.dataclasses.main import FlowStatus
from app.main.blueprints.deputydev_cli.app.ui.screens.dataclasses.main import AppContext


class FeatureResponseHandler:
    def __init__(
        self,
        feature_response: Union[FinalSuccessJob, FinalFailedJob],
        app_context: AppContext,
    ):
        self.feature_response = feature_response
        self.app_context = app_context

    def update_flow_context(self):
        if not isinstance(self.feature_response, FinalSuccessJob):
            raise ValueError("Flow context can only be updated for success response")
        if self.app_context.operation in [CLIFeatures.TASK_PLANNER]:
            self.app_context.current_status = FlowStatus.PLAN_GENERATED

        elif self.app_context.operation in [
            CLIFeatures.CODE_GENERATION,
            CLIFeatures.DOCS_GENERATION,
            CLIFeatures.TEST_GENERATION,
            CLIFeatures.PLAN_CODE_GENERATION,
        ]:
            self.app_context.current_status = FlowStatus.CODE_GENERATED

        elif self.app_context.operation in [CLIFeatures.GENERATE_AND_APPLY_DIFF]:
            if self.feature_response.pr_link:
                self.app_context.current_status = FlowStatus.PR_CREATED
            else:
                self.app_context.current_status = FlowStatus.DIFF_APPLIED

    async def _handle_success_response(self):
        if not isinstance(self.feature_response, FinalSuccessJob):
            raise ValueError("Success response should be of type FinalSuccessJob")
        if not self.app_context.local_repo:
            raise ValueError("Local repo not set in app context")
        if self.feature_response.display_response:
            print_formatted_text(FormattedText([("#32afff", self.feature_response.display_response)]))
        if self.feature_response.diff and not self.feature_response.pr_link:
            self.app_context.local_repo.apply_diff(self.feature_response.diff)
            if self.app_context.pr_config:
                print_formatted_text(FormattedText([("#729fcf", "Could not create PR. Applying diff locally...")]))
            else:
                print_formatted_text(FormattedText([("#729fcf", "Diff applied successfully")]))
        if (
            self.feature_response.pr_link
            and isinstance(self.app_context.local_repo, GitRepo)
            and self.app_context.pr_config
        ):
            if self.feature_response.existing_pr:
                print_formatted_text(
                    FormattedText(
                        [("#729fcf", f"Your changes will be visible in existing PR - {self.feature_response.pr_link}")]
                    )
                )
            else:
                print_formatted_text(
                    FormattedText([("#729fcf", f"PR created successfully - {self.feature_response.pr_link}")])
                )
            # sync local repo with remote if current branch is the source branch of PR config

            if self.app_context.pr_config.source_branch and self.app_context.registered_repo_details:
                current_branch = self.app_context.local_repo.get_active_branch()
                if self.app_context.local_repo.get_active_branch() != self.app_context.pr_config.source_branch:
                    self.app_context.local_repo.checkout_branch(self.app_context.pr_config.source_branch)
                try:
                    await self.app_context.local_repo.sync_with_remote(
                        branch_name=self.app_context.pr_config.source_branch,
                        remote_repo_url=self.app_context.registered_repo_details.repo_url,
                    )
                except Exception as e:
                    print_formatted_text(
                        FormattedText(
                            [("#ff0000", f"Error syncing local repo with remote: {str(e)}. Please sync manually")]
                        )
                    )
                finally:
                    if self.app_context.local_repo.get_active_branch() != current_branch:
                        self.app_context.local_repo.checkout_branch(current_branch)

    def _handle_failed_response(self):
        if not isinstance(self.feature_response, FinalFailedJob):
            raise ValueError("Failed response should be of type FinalFailedJob")
        if self.feature_response.display_message:
            print_formatted_text(self.feature_response.display_message)

    async def handle_response(self):
        if isinstance(self.feature_response, FinalSuccessJob):
            await self._handle_success_response()
            self.update_flow_context()
        else:
            self._handle_failed_response()
