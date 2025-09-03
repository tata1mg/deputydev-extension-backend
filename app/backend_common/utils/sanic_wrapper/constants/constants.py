from enum import StrEnum


class ENV:
    """Environment variables containing meta information about running service.

    Attributes:
        BRANCH: Current vcs branch from which service is deployed
        TAG: Release tag of service
    """

    GIT_BRANCH = "GIT_BRANCH"
    RELEASE_TAG = "RELEASE_TAG"


class Client(StrEnum):
    ANDROID = "android"
    IOS = "ios"
    WEB = "web"
    MWEB = "mweb"
    ADMIN = "admin"


HEALTHY_STATUS = "healthy"
UNHEALTHY_STATUS = "unhealthy"
