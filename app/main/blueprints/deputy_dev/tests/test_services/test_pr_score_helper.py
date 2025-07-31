import pytest

from app.main.blueprints.deputy_dev.services.code_review.common.helpers.pr_score_helper import (
    PRScoreHelper,
)


class TestPrScoreHelper:
    scenarios = [
        ({"name": "PR1", "issues": {}}, 1.0000),  # No issues (perfect PR)
        ({"name": "PR2", "issues": {1: 1}}, 1.0000),  # 1 minor issue
        ({"name": "PR3", "issues": {4: 1}}, 0.9800),  # 1 severe issue
        ({"name": "PR4", "issues": {4: 4}}, 0.9200),  # 4 severe issues
        ({"name": "PR5", "issues": {4: 10}}, 0.8000),  # 10 severe issues
        ({"name": "PR6", "issues": {4: 25}}, 0.5400),  # 25 severe issues
        ({"name": "PR7", "issues": {4: 50}}, 0.2400),  # 50 severe issues
        ({"name": "PR8", "issues": {4: 100}}, 0.0400),  # 100 severe issues
        ({"name": "PR9", "issues": {1: 20, 2: 15, 3: 10, 4: 5}}, 0.5400),  # Mixed weights
        ({"name": "PR10", "issues": {1: 40, 2: 30, 3: 20, 4: 10}}, 0.2400),  # Mixed weights, double of PR9
    ]

    @pytest.mark.parametrize("issues_data, score", scenarios)
    def test__calculate_pr_score(self, issues_data, score):
        assert PRScoreHelper.calculate_pr_score(issues_data["issues"]) == score
