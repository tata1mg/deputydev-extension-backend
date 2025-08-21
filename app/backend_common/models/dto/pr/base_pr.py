import re
from typing import Any, Dict


class BasePrModel:
    def __init__(self, scm: str, pr_detail: Dict[str, Any], meta_info: Dict[str, Any] | None = None) -> None:
        if meta_info is None:
            meta_info = dict()
        self.pr_detail = pr_detail
        self.meta_info = meta_info
        self.scm = scm

    def scm_type(self) -> str:
        return self.scm

    def workspace_id(self) -> str | None:
        return self.meta_info.get("workspace_id")

    def team_id(self) -> str | None:
        return self.meta_info.get("team_id")

    def pr_id(self) -> str | None:
        return self.meta_info.get("pr_id")

    def repo_id(self) -> str | None:
        return self.meta_info.get("repo_id")

    def review_status(self) -> str | None:
        return self.meta_info.get("review_status")

    def quality_score(self) -> float | None:
        return self.meta_info.get("quality_score")

    def scm_workspace_id(self) -> str | None:
        return self.meta_info.get("scm_workspace_id")

    def loc_changed(self) -> int | None:
        return self.meta_info.get("loc_changed")

    def pr_diff_token_count(self) -> int | None:
        return self.meta_info.get("pr_diff_token_count")

    def title(self) -> str | None:
        raise NotImplementedError()

    def description(self) -> str | None:
        raise NotImplementedError()

    def scm_pr_id(self) -> str | None:
        raise NotImplementedError()

    def scm_author_id(self) -> str | None:
        raise NotImplementedError()

    def scm_author_name(self) -> str | None:
        raise NotImplementedError()

    def scm_creation_time(self) -> str | None:
        raise NotImplementedError()

    def scm_close_time(self) -> str | None:
        raise NotImplementedError()

    def scm_state(self) -> str | None:
        raise NotImplementedError()

    def source_branch(self) -> str | None:
        raise NotImplementedError()

    def destination_branch(self) -> str | None:
        raise NotImplementedError()

    def scm_repo_id(self) -> str | None:
        raise NotImplementedError()

    def scm_repo_name(self) -> str | None:
        raise NotImplementedError()

    def scm_updation_time(self) -> str | None:
        raise NotImplementedError()

    def commit_id(self) -> str | None:
        raise NotImplementedError()

    def destination_branch_commit(self) -> str | None:
        raise NotImplementedError()

    def get_pr_info(self) -> Dict[str, Any]:
        pr_details: Dict[str, Any] = {
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
            "destination_commit_id": self.destination_branch_commit(),
        }
        return pr_details

    @staticmethod
    def user_description(description: str | None) -> str:
        if not description:
            return ""
        # Patterns to match start and end markers for the summary
        summary_start_pattern = r"DeputyDev generated PR summary:"
        summary_end_pattern = r"DeputyDev generated PR summary until (\[[a-f0-9]+\]\(https?://[^\)]+\)|[a-f0-9]+)"
        fallback_start_pattern = (
            r"\*\*Size \w+:\*\* This PR changes include \d+ lines and should take approximately [\d-]+ hours to review"
        )

        # Handle the current format with start and end markers
        summary_start_match = re.search(summary_start_pattern, description)
        summary_end_match = re.search(summary_end_pattern, description)
        if summary_start_match and summary_end_match:
            start_idx = summary_start_match.start()
            end_idx = summary_end_match.end()

            above_summary = description[:start_idx].replace("---", "").strip()
            below_summary = description[end_idx:].replace("---", "").strip()

            return f"{above_summary}\n\n{below_summary}".strip()

        # Handle fallback format (only size details are present and commit id info is not present)
        # We just add data added above the Deputydev generated summary in description
        fallback_start_match = re.search(fallback_start_pattern, description)
        if fallback_start_match:
            start_idx = fallback_start_match.start()
            above_summary = description[:start_idx].replace("---", "").strip()
            return above_summary.strip()

        return description
