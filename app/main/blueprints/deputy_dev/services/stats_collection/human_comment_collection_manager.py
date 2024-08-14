from app.common.utils.app_utils import convert_to_datetime
from app.main.blueprints.deputy_dev.constants.constants import MetaStatCollectionTypes
from app.main.blueprints.deputy_dev.services.experiment.experiment_service import (
    ExperimentService,
)
from app.main.blueprints.deputy_dev.services.stats_collection.stats_collection_base import (
    StatsCollectionBase,
)


class HumanCommentCollectionManager(StatsCollectionBase):
    def __init__(self, payload, query_params):
        super().__init__(payload, query_params)
        self.scm_pr_id = None
        self.is_human_count_incremented = False
        self.stats_type = MetaStatCollectionTypes.HUMAN_COMMENT.value

    def extract_payload(self):
        payload = {
            "scm_workspace_id": self.payload["repository"]["workspace"]["uuid"],
            "repo_name": self.payload["repository"]["name"],
            "scm_repo_id": self.payload["repository"]["uuid"],
            "actor": self.payload["actor"]["display_name"],
            "scm_pr_id": str(self.payload["pullrequest"]["id"]),
            "pr_created_at": convert_to_datetime(self.payload["pullrequest"]["created_on"]),
        }
        self.scm_pr_id = payload["scm_pr_id"]
        return payload

    async def save_to_db(self, payload):
        await self.get_pr_from_db(payload)
        self.is_human_count_incremented = await ExperimentService.increment_human_comment_count(
            scm_pr_id=self.scm_pr_id, repo_id=self.repo_dto.id
        )

    async def revert(self):
        if self.repo_dto and self.is_human_count_incremented:
            await ExperimentService.decrement_human_comment_count(scm_pr_id=self.scm_pr_id, repo_id=self.repo_dto.id)
