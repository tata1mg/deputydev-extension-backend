from sanic.log import logger

from app.main.blueprints.deputy_dev.constants.constants import MetaStatCollectionTypes
from app.main.blueprints.deputy_dev.services.stats_collection.human_comment_collection_manager import (
    HumanCommentCollectionManager,
)
from app.main.blueprints.deputy_dev.services.stats_collection.pr_approval_time_manager import (
    PRApprovalTimeManager,
)
from app.main.blueprints.deputy_dev.services.stats_collection.pullrequest_metrics_manager import (
    PullRequestMetricsManager,
)


class StatsCollectionFactory:
    FACTORIES = {
        MetaStatCollectionTypes.PR_CLOSE.value: PullRequestMetricsManager,
        MetaStatCollectionTypes.HUMAN_COMMENT.value: HumanCommentCollectionManager,
        MetaStatCollectionTypes.PR_APPROVAL_TIME.value: PRApprovalTimeManager,
    }

    @classmethod
    async def handle_event(cls, data):
        event_type = data.get(
            "stats_type", MetaStatCollectionTypes.PR_CLOSE.value
        )  # default value for backward compatibility
        logger.info(f"Received New SQS Message for meta sync {event_type}")
        _klass = cls.FACTORIES[event_type]

        payload = data.get("payload")
        query_params = data.get("query_params") or {}
        await _klass(payload=payload, query_params=query_params).process_event()
