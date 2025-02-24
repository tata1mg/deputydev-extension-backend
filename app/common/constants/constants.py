from enum import Enum

from deputydev_core.utils.config_manager import ConfigManager

PR_SUMMARY_TEXT = "\n\n **DeputyDev generated PR summary:** \n\n"
PR_SIZING_TEXT = (
    "\n\n **Size {category}:** This PR changes include {loc} lines and should take approximately {time}\n\n"
)
PR_SUMMARY_COMMIT_TEXT = "DeputyDev generated PR summary until {commit_id}"
PR_NOT_FOUND = "PR does not exist"
LARGE_PR_DIFF = "PR diff is larger than 20k lines"
MAX_RELEVANT_CHUNKS = ConfigManager.configs["CHUNKING"]["NUMBER_OF_CHUNKS"]
IS_LLM_RERANKING_ENABLED = ConfigManager.configs["CHUNKING"]["IS_LLM_RERANKING_ENABLED"]
MAX_ITERATIVE_CHUNKS = 20

CUSTOM_PROMPT_CHAR_LIMIT = 4000


class SettingErrorType(Enum):
    INVALID_SETTING = "INVALID_SETTING"
    CUSTOM_PROMPT_LENGTH_EXCEED = "CUSTOM_PROMPT_LENGTH_EXCEED"
    INVALID_CHAT_SETTING = "INVALID_CHAT_SETTING"
    INVALID_TOML = "INVALID_TOML"
    MISSING_KEY = "MISSING_KEY"


SETTING_ERROR_MESSAGE = {
    SettingErrorType.INVALID_TOML.value: "Default settings applied as deputydev.toml file is not a valid toml file.\n\nErrors:",
    SettingErrorType.INVALID_SETTING.value: "Default settings applied as custom settings validation failed.\n\nErrors:",
    SettingErrorType.CUSTOM_PROMPT_LENGTH_EXCEED.value: f"Default prompts are getting used for following agents as their custom prompt exceed defined limit of {CUSTOM_PROMPT_CHAR_LIMIT} characters:\n\n",
    SettingErrorType.INVALID_CHAT_SETTING.value: f"Default prompt is getting used for chat as Custom Prompt exceed the defined limit of {CUSTOM_PROMPT_CHAR_LIMIT} characters",
    SettingErrorType.MISSING_KEY.value: "Invalid override or creation of agents due to missing mandatory keys. Default settings are applied for invalid pre-defined agents, while invalid custom agents are skipped. \n\nInvalid Agents:\n\n",
}


class TimeFormat(Enum):
    SECONDS = "SECONDS"
    MINUTES = "MINUTES"


class VCSFailureMessages(Enum):
    BITBUCKET_PR_UPDATE_FAIL = "Can only update an open pull request."
    GITHUB_VALIDATION_FAIL = "Validation Failed"
    GITHUB_INCORRECT_LINE_NUMBER = "pull_request_review_thread.line"
    GITHUB_INCORRECT_FILE_PATH = "pull_request_review_thread.path"


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
RUBY_EXTENSIONS = {"rb": "ruby"}
KOTLIN_EXTENSIONS = {"kt": "kotlin"}

# We collect all the language dictionaries and create a single dict, making it easier to segregate as different extensions
# can be served from the same programming language
ALL_EXTENSIONS = {
    **JAVASCRIPT_EXTENSIONS,
    **TYPESCRIPT_EXTENSIONS,
    **JAVA_EXTENSIONS,
    **TSX_EXTENSIONS,
    **EXTENSION_TO_LANGUAGE,
    **RUBY_EXTENSIONS,
    **KOTLIN_EXTENSIONS,
}


class LLMProviders(Enum):
    OPENAI = "OPENAI"
    ANTHROPIC = "ANTHROPIC"


class TokenableType(str, Enum):
    TEAM = "team"
    INTEGRATION = "integration"
    WORKSPACE = "workspace"


class TokenType(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"
    INSTALLATION = "installation"  # github instalation id
    WORKSPACE_ACCESS = "workspace_access"


class VCSTypes(str, Enum):
    bitbucket = "bitbucket"
    gitlab = "gitlab"
    github = "github"


class PRStatus(Enum):
    OPEN = "OPEN"
    MERGED = "MERGED"
    DECLINED = "DECLINED"
    APPROVED = "approved"
