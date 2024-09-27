class BasePrModel:
    def __init__(self, scm: str, pr_detail: dict, meta_info: dict = None):
        if meta_info is None:
            meta_info = dict()
        self.pr_detail = pr_detail
        self.meta_info = meta_info
        self.scm = scm

    def scm_type(self):
        return self.scm

    def workspace_id(self):
        return self.meta_info.get("workspace_id")

    def team_id(self):
        return self.meta_info.get("team_id")

    def pr_id(self):
        return self.meta_info.get("pr_id")

    def repo_id(self):
        return self.meta_info.get("repo_id")

    def review_status(self):
        return self.meta_info.get("review_status")

    def quality_score(self):
        return self.meta_info.get("quality_score")

    def scm_workspace_id(self):
        return self.meta_info.get("scm_workspace_id")

    def loc_changed(self):
        return self.meta_info.get("loc_changed")

    def pr_diff_token_count(self):
        return self.meta_info.get("pr_diff_token_count")

    def title(self):
        raise NotImplementedError()

    def description(self):
        raise NotImplementedError()

    def scm_pr_id(self):
        raise NotImplementedError()

    def scm_author_id(self):
        raise NotImplementedError()

    def scm_author_name(self):
        raise NotImplementedError()

    def scm_creation_time(self):
        raise NotImplementedError()

    def scm_close_time(self):
        raise NotImplementedError()

    def scm_state(self):
        raise NotImplementedError()

    def source_branch(self):
        raise NotImplementedError()

    def destination_branch(self):
        raise NotImplementedError()

    def scm_repo_id(self):
        raise NotImplementedError()

    def scm_repo_name(self):
        raise NotImplementedError()

    def scm_updation_time(self):
        raise NotImplementedError()

    def commit_id(self):
        raise NotImplementedError()

    def get_pr_info(self) -> dict:
        pr_details = {
            "quality_score": self.quality_score(),
            "title": self.title(),
            "description": self.description(),
            "team_id": self.team_id(),
            "scm_pr_id": str(self.scm_pr_id()),
            "scm_author_id": self.scm_author_id(),
            "author_name": self.scm_author_name(),
            "scm_creation_time": self.scm_creation_time(),
            "review_status": self.review_status(),
            "scm": self.scm_type(),
            "workspace_id": self.workspace_id(),
            "repo_id": self.repo_id(),
            "source_branch": self.source_branch(),
            "destination_branch": self.destination_branch(),
            "commit_id": self.commit_id(),
            "loc_changed": self.loc_changed(),
        }
        return pr_details
