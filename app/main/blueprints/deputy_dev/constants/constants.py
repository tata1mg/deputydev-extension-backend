from enum import Enum

from torpedo.common_utils import CONFIG

from app.common.constants.constants import ExtendedEnum

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
SCRIT_TAG = "#scrit"
SCRIT_DEPRECATION_NOTIFICATION = (
    "Note :- #scrit is deprecated and will be removed with next releases. Recommended to use - #deputydev or #dd"
)


class LLMModels(Enum):
    Summarization = "SCRIT_MODEL"
    FoundationModel = "SCRIT_MODEL"
    FinetunedModel = "FINETUNED_SCRIT_MODEL"


class SCMType(Enum):
    BITBUCKET = "bitbucket"
    GITHUB = "github"
    GITLAB = "gitlab"


class PrStatusTypes(Enum):
    IN_PROGRESS = "IN_PROGRESS"  # Eligible for experiment
    COMPLETED = "COMPLETED"  # Eligible for experiment
    REJECTED_EXPERIMENT = "REJECTED_EXPERIMENT"  # Eligible for experiment
    REJECTED_LARGE_SIZE = "REJECTED_LARGE_SIZE"
    REJECTED_ALREADY_MERGED = "REJECTED_ALREADY_MERGED"
    REJECTED_ALREADY_DECLINED = "REJECTED_ALREADY_DECLINED"
    REJECTED_NO_DIFF = "REJECTED_NO_DIFF"
    REJECTED_CLONING_FAILED_WITH_128 = "REJECTED_CLONING_FAILED_WITH_128"
    REJECTED_INVALID_REQUEST = "REJECTED_INVALID_REQUEST"
    FAILED = "FAILED"


class LLMCommentTypes(Enum):
    FINE_TUNED_COMMENTS = "finetuned_comments"
    FOUNDATION_COMMENTS = "foundation_comments"


class BucketTypes(Enum):
    ISSUE = "issue"
    SUGGESTION = "suggestion"


class BucketStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class TokenTypes(Enum):
    PR_DIFF_TOKENS = "pr_diff_tokens"
    REVIEW_CONTEXT = "user_context"
    RELEVANT_CHUNK = "relevant_chunk"
    EMBEDDING = "embedding"
    PR_SUMMARY_MODEL_INPUT = "pr_summary_input"
    PR_SUMMARY_MODEL_OUTPUT = "pr_summary_output"
    PR_REVIEW_MODEL_OUTPUT = "pr_review_model_output"
    PR_REVIEW_MODEL_INPUT = "pr_review_model_input"
    PR_TITLE = "pr_title"
    PR_DESCRIPTION = "pr_description"
    PR_CONFLUENCE = "pr_confluence"
    PR_USER_STORY = "pr_user_story"
    PR_REVIEW_SYSTEM_PROMPT = "pr_review_system_prompt"
    PR_REVIEW_USER_PROMPT = "pr_review_user_prompt"


class FeedbackTypes(ExtendedEnum):
    LIKE = "like"
    DISLIKE = "dislike"
    SUGGESTION = "suggestion"


class ChatTypes(ExtendedEnum):
    DEPUTY_DEV = "deputydev"
    SCRIT = "scrit"
    DD = "dd"


class MessageTypes(Enum):
    CHAT = "chat"
    FEEDBACK = "feedback"
    UNKNOWN = "unknown"


class PRReviewExperimentSet(Enum):
    ReviewTest = "TestSet"
    ReviewControl1 = "ControlSet1"
    ReviewControl2 = "ControlSet2"


MODEL_MAPPING = {
    LLMCommentTypes.FINE_TUNED_COMMENTS.value: LLMModels.FinetunedModel.value,
    LLMCommentTypes.FOUNDATION_COMMENTS.value: LLMModels.FoundationModel.value,
}


class LLMModelNames(ExtendedEnum):
    GPT_3_5_TURBO = "gpt-3.5-turbo"
    GPT_4 = "gpt-4"
    GPT_4_PREVIEW = "gpt-4-1106-preview"
    GPT_4_O = "gpt-4o"
    GPT_TEXT_EMBEDDING_3_SMALL = "text-embedding-3-small"


class ExperimentStatusTypes(Enum):
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class PRStatus(Enum):
    OPEN = "OPEN"
    MERGED = "MERGED"
    DECLINED = "DECLINED"
