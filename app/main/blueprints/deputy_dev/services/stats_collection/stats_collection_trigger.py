from torpedo import CONFIG

from app.main.blueprints.deputy_dev.constants.constants import (
    MetaStatCollectionTypes,
    PRStatus,
)
from app.main.blueprints.deputy_dev.constants.repo import VCSTypes
from app.main.blueprints.deputy_dev.services.sqs.meta_subscriber import MetaSubscriber


class StatsCollectionTrigger:
    config = CONFIG.config

    @classmethod
    async def select_stats_and_publish(cls, payload, query_params):
        vcs_type = query_params.get("vcs_type", VCSTypes.bitbucket.value)
        stats_type = cls.get_stats_collection_type(vcs_type, payload)
        data = {"payload": payload, "query_params": query_params, "stats_type": stats_type}
        await MetaSubscriber(config=cls.config).publish(data)

    @classmethod
    def get_stats_collection_type(cls, vcs_type, payload):
        if vcs_type == VCSTypes.bitbucket.value:
            return cls.bitbucket_stat_type(payload)

    @classmethod
    def bitbucket_stat_type(cls, payload):
        if payload.get("pullrequest", {}).get("state") in [PRStatus.MERGED.value, PRStatus.DECLINED.value]:
            return MetaStatCollectionTypes.PR_CLOSE.value
        if payload.get("comment"):
            return MetaStatCollectionTypes.HUMAN_COMMENT.value
