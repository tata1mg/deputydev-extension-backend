from app.backend_common.models.dto.pr.base_pr import BasePrModel
from app.backend_common.constants.constants import PRStatus, VCSTypes


class GitlabPrModel(BasePrModel):
    def __init__(self, pr_detail: dict, meta_info: dict = None):
        super().__init__(scm=VCSTypes.gitlab.value, pr_detail=pr_detail, meta_info=meta_info)

    def title(self):
        return self.pr_detail["title"]

    def description(self):
        return self.user_description(self.pr_detail["description"])

    def scm_pr_id(self):
        return self.pr_detail["iid"]

    def scm_author_id(self):
        return str(self.pr_detail["author"]["id"])

    def scm_author_name(self):
        return self.pr_detail["author"]["name"]

    def scm_creation_time(self):
        return self.pr_detail["created_at"].replace("Z", "+00:00")

    def scm_updation_time(self):
        return self.pr_detail["updated_at"].replace("Z", "+00:00")

    def scm_close_time(self):
        return self.pr_detail["closed_at"].replace("Z", "+00:00") if self.pr_detail["closed_at"] else None

    def scm_state(self):
        scm_state = self.pr_detail["state"]
        if scm_state == "opened":
            return PRStatus.OPEN.value
        elif scm_state == "merged":
            return PRStatus.MERGED.value
        else:
            return PRStatus.DECLINED.value

    def source_branch(self):
        return self.pr_detail["source_branch"]

    def destination_branch(self):
        return self.pr_detail["target_branch"]

    def commit_id(self):
        return self.pr_detail["sha"]

    def scm_repo_name(self):
        return str(self.pr_detail["repo_name"])

    def scm_repo_id(self):
        return str(self.pr_detail["project_id"])

    def diff_refs(self):
        return self.pr_detail["diff_refs"]

    def destination_branch_commit(self):
        return self.pr_detail["diff_refs"]["base_sha"]
