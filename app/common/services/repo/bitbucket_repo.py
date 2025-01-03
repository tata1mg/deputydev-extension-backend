from typing import Optional, Tuple

from app.common.service_clients.bitbucket import BitbucketRepoClient
from app.common.services.credentials import AuthHandler
from app.common.services.repo.base_repo import BaseRepo
from app.main.blueprints.deputy_dev.constants.repo import VCS_REPO_URL_MAP, VCSTypes


class BitbucketRepo(BaseRepo):
    def __init__(
        self,
        workspace: str,
        repo_name: str,
        workspace_id: str,
        auth_handler: AuthHandler,
        workspace_slug: str,
        repo_id: str = None,
    ):
        super().__init__(
            vcs_type=VCSTypes.bitbucket.value,
            workspace=workspace,
            repo_name=repo_name,
            workspace_id=workspace_id,
            workspace_slug=workspace_slug,
            repo_id=repo_id,
            auth_handler=auth_handler,
        )
        self.repo_client = BitbucketRepoClient(
            workspace_slug=workspace_slug,
            repo=repo_name,
            pr_id=None,
            auth_handler=auth_handler,
        )
        self.token = ""

    async def get_repo_url(self):
        self.token = await self.auth_handler.access_token()
        return VCS_REPO_URL_MAP[self.vcs_type].format(
            token=self.token, workspace_slug=self.workspace_slug, repo_name=self.repo_name
        )

    def get_remote_url_without_token(self):
        return f"git@bitbucket.org:{self.workspace_slug}/{self.repo_name}.git"

    async def is_pr_open_between_branches(
        self, source_branch: str, destination_branch: str
    ) -> Tuple[bool, Optional[str]]:
        prs = await self.repo_client.list_prs()
        existing_pr = (
            next(
                (
                    pr
                    for pr in prs["values"]
                    if pr["source"]["branch"]["name"] == source_branch
                    and pr["destination"]["branch"]["name"] == destination_branch
                ),
                None,
            )
            if prs and prs.get("values")
            else None
        )
        pr_url = existing_pr["links"]["html"]["href"] if existing_pr else None
        return bool(existing_pr), pr_url

    async def create_issue_comment(self, issue_id: str, comment: str):
        await self.repo_client.create_issue_comment(issue_id, comment)

    def get_repo_actor(self):
        return self.auth_handler.get_git_actor()
