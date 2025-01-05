from app.backend_common.models.dto.pr.base_pr import BasePrModel
from app.common.constants.constants import PRStatus, VCSTypes


class GitHubPrModel(BasePrModel):
    def __init__(self, pr_detail: dict, meta_info: dict = None):
        super().__init__(scm=VCSTypes.github.value, pr_detail=pr_detail, meta_info=meta_info)

    def title(self):
        return self.pr_detail["title"]

    def description(self):
        return self.pr_detail["body"] or ""

    def scm_pr_id(self):
        return self.pr_detail["number"]

    def scm_author_id(self):
        return str(self.pr_detail["user"]["id"])

    def scm_author_name(self):
        return self.pr_detail["user"]["login"]

    def scm_creation_time(self):
        return self.pr_detail["created_at"].replace("Z", "+00:00")

    def scm_updation_time(self):
        return self.pr_detail["updated_at"].replace("Z", "+00:00")

    def scm_close_time(self):
        return self.pr_detail["updated_at"].replace("Z", "+00:00")

    def scm_state(self):
        scm_state = self.pr_detail["state"]
        if scm_state == "open":
            return PRStatus.OPEN.value
        elif scm_state == "closed":
            return PRStatus.MERGED.value
        else:
            return PRStatus.DECLINED.value

    def source_branch(self):
        return self.pr_detail["head"]["ref"]

    def destination_branch(self):
        return self.pr_detail["base"]["ref"]

    def commit_id(self):
        return self.pr_detail["head"]["sha"]

    def scm_repo_name(self):
        return str(self.pr_detail["head"]["repo"]["name"])

    def scm_repo_id(self):
        return str(self.pr_detail["head"]["repo"]["id"])

    def destination_branch_commit(self):
        return self.pr_detail["base"]["sha"]
