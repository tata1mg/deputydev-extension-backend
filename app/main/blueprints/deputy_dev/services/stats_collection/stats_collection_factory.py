from copy import deepcopy
from typing import Any, Dict

from sanic.log import logger

from app.backend_common.constants.constants import VCSTypes
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
    async def handle_event(cls, data: Dict[str, Any]) -> None:
        event_type = data.get(
            "stats_type", MetaStatCollectionTypes.PR_CLOSE.value
        )  # default value for backward compatibility
        logger.info(f"Received New SQS Message for meta sync {event_type}")

        payload = data.get("payload")
        # TODO Added for backward compatibility, remove later.
        vcs_type = data.get("vcs_type") or VCSTypes.bitbucket.value
        _klass = cls.FACTORIES[event_type](payload=deepcopy(payload), vcs_type=vcs_type)

        if _klass.validate_payload():
            await _klass.process_event()
        else:
            # TODO Deprecated code added just for backward compatibility
            await _klass.generate_old_payload()
            await _klass.process_event()
