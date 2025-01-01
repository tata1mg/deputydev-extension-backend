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


class PromptFeatures(Enum):
    CODE_GENERATION = "CODE_GENERATION"
    CODE_REVIEW = "CODE_REVIEW"
    RE_RANKING = "RE_RANKING"
    TEST_GENERATION = "TEST_GENERATION"
    DOCS_GENERATION = "DOCS_GENERATION"
    CHUNK_DESCRIPTION_GENERATION = "CHUNK_DESCRIPTION_GENERATION"
    TASK_PLANNER = "TASK_PLANNER"
    TEST_PLAN_GENERATION = "TEST_PLAN_GENERATION"
    ITERATIVE_CODE_CHAT = "ITERATIVE_CODE_CHAT"
    DIFF_CREATION = "DIFF_CREATION"
    PLAN_CODE_GENERATION = "PLAN_CODE_GENERATION"


class LLModels(Enum):
    GPT_4O = "GPT_4O"
    CLAUDE_3_POINT_5_SONNET = "CLAUDE_3_POINT_5_SONNET"


class Connections(Enum):
    DEPUTY_DEV_REPLICA = "deputy_dev_replica"


JAVASCRIPT_EXTENSIONS = {
    "js": "javascript",
    "jsx": "javascript",
    "mjs": "javascript",
    "cjs": "javascript",
    "es": "javascript",
    "es6": "javascript",
}
EXTENSION_TO_LANGUAGE = {"py": "python", "html": "html", "kt": "kotlin", "go": "go", "json": "json"}
TSX_EXTENSIONS = {"tsx": "tsx"}
JAVA_EXTENSIONS = {"java": "java"}
TYPESCRIPT_EXTENSIONS = {
    "ts": "typescript",
    "mts": "typescript",
    "cts": "typescript",
}


# We collect all the language dictionaries and create a single dict, making it easier to segregate as different extensions
# can be served from the same programming language
ALL_EXTENSIONS = {
    **JAVASCRIPT_EXTENSIONS,
    **TYPESCRIPT_EXTENSIONS,
    **JAVA_EXTENSIONS,
    **TSX_EXTENSIONS,
    **EXTENSION_TO_LANGUAGE,
}
