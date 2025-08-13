from typing import Any, Dict

from app.backend_common.constants.constants import PRStatus, VCSTypes
from app.backend_common.models.dto.pr.base_pr import BasePrModel


class GitHubPrModel(BasePrModel):
    def __init__(self, pr_detail: Dict[str, Any], meta_info: Dict[str, Any] | None = None) -> None:
        super().__init__(scm=VCSTypes.github.value, pr_detail=pr_detail, meta_info=meta_info)

    def title(self) -> str:
        return self.pr_detail["title"]

    def description(self) -> str:
        return self.user_description(self.pr_detail["body"]) or ""

    def scm_pr_id(self) -> str:
        return self.pr_detail["number"]

    def scm_author_id(self) -> str:
        return str(self.pr_detail["user"]["id"])

    def scm_author_name(self) -> str:
        return self.pr_detail["user"]["login"]

    def scm_creation_time(self) -> str:
        return self.pr_detail["created_at"].replace("Z", "+00:00")

    def scm_updation_time(self) -> str:
        return self.pr_detail["updated_at"].replace("Z", "+00:00")

    def scm_close_time(self) -> str:
        return self.pr_detail["updated_at"].replace("Z", "+00:00")

    def scm_state(self) -> str:
        scm_state = self.pr_detail["state"]
        if scm_state == "open":
            return PRStatus.OPEN.value
        elif scm_state == "closed":
            return PRStatus.MERGED.value
        else:
            return PRStatus.DECLINED.value

    def source_branch(self) -> str:
        return self.pr_detail["head"]["ref"]

    def destination_branch(self) -> str:
        return self.pr_detail["base"]["ref"]

    def commit_id(self) -> str:
        return self.pr_detail["head"]["sha"]

    def scm_repo_name(self) -> str:
        return str(self.pr_detail["head"]["repo"]["name"])

    def scm_repo_id(self) -> str:
        return str(self.pr_detail["head"]["repo"]["id"])

    def destination_branch_commit(self) -> str:
        return self.pr_detail["base"]["sha"]
