from enum import Enum


class TimeFormat(Enum):
    SECONDS = "SECONDS"
    MINUTES = "MINUTES"


class ExtendedEnum(Enum):
    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))


class VCSFailureMessages(Enum):
    BITBUCKET_PR_UPDATE_FAIL = "Can only update an open pull request."
    GITHUB_VALIDATION_FAIL = "Validation Failed"
    GITHUB_INCORRECT_LINE_NUMBER = "pull_request_review_thread.line"
    GITHUB_INCORRECT_FILE_PATH = "pull_request_review_thread.path"


class Connections(Enum):
    DEPUTY_DEV_REPLICA = "deputy_dev_replica"
