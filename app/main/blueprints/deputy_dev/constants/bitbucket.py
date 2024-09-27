from enum import Enum


class WebhookEvent(str, Enum):
    PULLREQUEST_CREATED = "pullrequest:created"
    PULLREQUEST_UPDATED = "pullrequest:updated"
    PULLREQUEST_MERGED = "pullrequest:fulfilled"
    PULLREQUEST_DECLINED = "pullrequest:rejected"
    # -- pr comments --
    COMMENT_CREATED = "pullrequest:comment_created"
    COMMENT_UPDATED = "pullrequest:comment_updated"
    COMMENT_DELETED = "pullrequest:comment_deleted"
