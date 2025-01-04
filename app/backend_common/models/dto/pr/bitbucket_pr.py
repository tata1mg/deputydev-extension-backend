from app.backend_common.models.dto.pr.base_pr import BasePrModel
from app.backend_common.utils.app_utils import get_vcs_repo_name_slug
from app.common.constants.constants import VCSTypes


class BitbucketPrModel(BasePrModel):
    def __init__(self, pr_detail: dict, meta_info: dict = None):
        super().__init__(scm=VCSTypes.bitbucket.value, pr_detail=pr_detail, meta_info=meta_info)

    def title(self):
        return self.pr_detail["title"]

    def description(self):
        return self.pr_detail["description"]

    def scm_pr_id(self):
        return self.pr_detail["id"]

    def scm_author_id(self):
        return self.pr_detail["author"]["uuid"]

    def scm_author_name(self):
        return self.pr_detail["author"]["display_name"]

    def scm_creation_time(self):
        return self.pr_detail["created_on"].replace("Z", "+00:00")

    def scm_updation_time(self):
        return self.pr_detail["updated_on"].replace("Z", "+00:00")

    def scm_close_time(self):
        return self.pr_detail["updated_on"].replace("Z", "+00:00")

    def scm_state(self):
        return self.pr_detail["state"]

    def source_branch(self):
        return self.pr_detail["source"]["branch"]["name"]

    def destination_branch(self):
        return self.pr_detail["destination"]["branch"]["name"]

    def commit_id(self):
        return self.pr_detail["source"]["commit"]["hash"]

    def scm_repo_id(self):
        return self.pr_detail["destination"]["repository"]["uuid"]

    def scm_repo_name(self):
        return get_vcs_repo_name_slug(self.pr_detail["destination"]["repository"]["full_name"])

    def destination_branch_commit(self):
        return self.pr_detail["destination"]["commit"]["hash"]
