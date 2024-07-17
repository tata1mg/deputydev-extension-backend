from enum import Enum

from torpedo.common_utils import CONFIG

MAX_PR_DIFF_TOKEN_LIMIT = CONFIG.config["MAX_PR_DIFF_TOKEN_LIMIT"]
IGNORE_FILES = CONFIG.config["IGNORE_FILES"]
COMMENTS_DEPTH = 7
PR_SIZE_TOO_BIG_MESSAGE = (
    "Ideal pull requests are not more than 50 lines. PRs with smaller diff are merged relatively "
    "quickly and have much lower chances of getting reverted. This PR was found to have a diff token count "
    "of {pr_diff_token_count} as a result of which it exceeded the max token count limit. SCRIT will only review PRs having total token count of not more than {max_token_limit}."
    " Note :- Every 4 characters is equal to 1 token."
)
BATCH_SIZE = CONFIG.config["BATCH_SIZE"]
TAGS = ["#scrit", "#deputydev", "#dd"]
SCRIT_DEPRECATION_NOTIFICATION = (
    "Note :- #scrit is deprecated and will be removed with next releases. Recommended to use - #deputydev or #dd"
)


class LLMModels(Enum):
    Summarization = "SCRIT_MODEL"
    FoundationModel = "SCRIT_MODEL"
    FinetunedModel = "FINETUNED_SCRIT_MODEL"
