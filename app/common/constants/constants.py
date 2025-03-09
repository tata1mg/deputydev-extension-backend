from enum import Enum


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
