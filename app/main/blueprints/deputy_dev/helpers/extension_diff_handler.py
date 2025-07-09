from typing import List, Set
from app.backend_common.utils.app_utils import get_token_count
import re


class ExtensionDiffHandler:
    def __init__(self, pr_diff: str):
        self.pr_diff = pr_diff
        self.diff_git_re = re.compile(r"^diff --git a/(.+?) b/(.+)$")

    def get_diff_loc(self) -> int:
        """
        Calculate total lines added and removed in the PR diff.
        Ignores diff metadata lines.
        """
        added = 0
        removed = 0
        for line in self.pr_diff.splitlines():
            if line.startswith("+++") or line.startswith("---"):
                continue
            if line.startswith("+") and not line.startswith("+++"):
                added += 1
            elif line.startswith("-") and not line.startswith("---"):
                removed += 1
        return added + removed

    def get_files(self) -> List[str]:
        """
        Extract the list of files touched by this diff, in the order they appear.
        - On deletion, returns the old path.
        - On rename, returns only the new path.
        - Skips `/dev/null` placeholders.
        """
        seen_files = set()
        changed_files: List[str] = []

        for line in self.pr_diff.splitlines():
            match = self.diff_git_re.match(line)
            if not match:
                continue

            old_path, new_path = match.groups()
            # prefer new path unless it's /dev/null
            selected_path = new_path if new_path != "/dev/null" else old_path

            if selected_path not in seen_files:
                seen_files.add(selected_path)
                changed_files.append(selected_path)

        return changed_files

    def get_diff_token_count(self) -> int:
        """
        Returns the token count for the PR diff using the shared utility.
        """
        return get_token_count(self.pr_diff)
