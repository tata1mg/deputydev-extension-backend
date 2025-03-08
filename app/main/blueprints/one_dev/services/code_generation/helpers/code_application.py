from typing import Dict, List, Optional, Tuple

from deputydev_core.utils.context_vars import set_context_values
from sanic.log import logger

from app.backend_common.services.pr.pr_factory import PRFactory
from app.backend_common.services.repo.base_repo import BaseRepo


class CodeApplicationHandler:
    def __init__(
        self,
        repo_path: str,
        repo_service: BaseRepo,
        diff: Dict[str, List[Tuple[int, int, str]]],
        commit_message: str,
        pr_title: str,
    ):
        self.repo_path = repo_path
        self.repo_service = repo_service
        self.diff = diff
        self.commit_message = commit_message
        self.pr_title = pr_title
        self.is_diff_applied = False

    async def create_or_update_pr(
        self,
        destination_branch: str,
        source_branch: str,
        pr_title_prefix: Optional[str] = None,
        commit_message_prefix: Optional[str] = None,
    ) -> Tuple[bool, str]:
        # set default values for commit message and pr title prefix
        commit_message_prefix = commit_message_prefix or ""
        pr_title_prefix = pr_title_prefix or ""

        self.repo_service.checkout_branch(source_branch)

        # apply diff on local repo if not already applied
        if not self.is_diff_applied:
            self.apply_diff()

        # commit changes and push to remote
        self.repo_service.stage_changes()
        self.repo_service.commit_changes(commit_message=commit_message_prefix + self.commit_message)
        await self.repo_service.push_to_remote(source_branch)

        # create PR if no PR is open between source and destination branches
        pr_link: Optional[str] = None
        existing_pr: bool = True
        try:
            is_pr_open_between_branches, pr_link = await self.repo_service.is_pr_open_between_branches(
                source_branch, destination_branch
            )
            if not is_pr_open_between_branches:
                existing_pr = False
                set_context_values(dd_workspace_id=self.repo_service.workspace_id)
                pr_link = await (
                    await PRFactory.pr(
                        vcs_type=self.repo_service.vcs_type,
                        repo_name=self.repo_service.repo_name,
                        pr_id=None,
                        workspace=self.repo_service.workspace,
                        workspace_slug=self.repo_service.workspace_slug,
                        workspace_id=self.repo_service.workspace_id,
                        auth_handler=self.repo_service.auth_handler,
                        repo_service=self.repo_service,
                    )
                ).create_pr(
                    title=pr_title_prefix + self.pr_title,
                    description="",
                    source_branch=source_branch,
                    destination_branch=destination_branch,
                )

        except Exception as e:
            logger.exception(f"Error creating PR: {str(e)}")
            raise e

        if not pr_link:
            raise ValueError("Error creating PR, PR link not found")

        return existing_pr, pr_link

    def apply_diff(self):
        self.repo_service.apply_diff_on_local_repo(self.diff)
        self.is_diff_applied = True
