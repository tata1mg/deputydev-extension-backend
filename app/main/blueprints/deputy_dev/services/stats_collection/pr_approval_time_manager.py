from app.common.utils.app_utils import convert_to_datetime
from app.main.blueprints.deputy_dev.services.pr.pr_service import PRService
from app.main.blueprints.deputy_dev.services.stats_collection.stats_collection_base import (
    StatsCollectionBase,
)


class PRApprovalTimeManager(StatsCollectionBase):
    def __init__(self, payload, query_params):
        super().__init__(payload, query_params)

    def extract_payload(self):
        payload = {
            "scm_workspace_id": self.payload["repository"]["workspace"]["uuid"],
            "repo_name": self.payload["repository"]["name"],
            "scm_repo_id": self.payload["repository"]["uuid"],
            "actor": self.payload["actor"]["display_name"],
            "scm_pr_id": str(self.payload["pullrequest"]["id"]),
            "scm_approval_time": self.payload["approval"]["date"],
        }
        return payload

    async def save_to_db(self, payload):
        await self.get_pr_from_db(payload)
        await PRService.db_update(
            payload={"scm_approval_time": convert_to_datetime(payload["scm_approval_time"])},
            filters={"id": self.pr_dto.id},
        )
