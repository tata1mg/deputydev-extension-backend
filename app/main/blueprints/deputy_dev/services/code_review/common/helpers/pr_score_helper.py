import math
from typing import Dict


class PRScoreHelper:
    @classmethod
    def calculate_pr_score(cls, issues: Dict[int, int]) -> int:
        return cls.__format_score(cls.__calculate_pr_score(issues))

    @classmethod
    def __scaling_factor(cls) -> float:
        return 100.0

    @classmethod
    def __format_score(cls, score: float) -> int:
        return int(score * cls.__scaling_factor())

    @classmethod
    def __calculate_pr_score(cls, issues: Dict[int, int]) -> float:
        weighted_score = sum(weight * count for weight, count in issues.items())
        total_comments = sum(issues.values())
        if total_comments == 0:
            return 1.0  # Perfect score for PRs with no issues
        # Use sigmoid function to map score to (0, 1) range
        return 2 * (1 - (1 / (1 + math.exp(-0.01 * weighted_score))))
