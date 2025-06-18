from enum import Enum


class CLIOperations(Enum):
    CODE_GENERATION = "CODE_GENERATION"
    TEST_GENERATION = "TEST_GENERATION"
    DOCS_GENERATION = "DOCS_GENERATION"
    TASK_PLANNER = "TASK_PLANNER"


class CLIFeatures(Enum):
    CODE_GENERATION = CLIOperations.CODE_GENERATION.value
    TEST_GENERATION = CLIOperations.TEST_GENERATION.value
    DOCS_GENERATION = CLIOperations.DOCS_GENERATION.value
    TASK_PLANNER = CLIOperations.TASK_PLANNER.value
    ITERATIVE_CHAT = "ITERATIVE_CHAT"
    GENERATE_AND_APPLY_DIFF = "GENERATE_AND_APPLY_DIFF"
    PLAN_CODE_GENERATION = "PLAN_CODE_GENERATION"


class AuthTokenConstants(Enum):
    CLI_AUTH_TOKEN = "cli_auth_token"


class LocalDirectories(Enum):
    LOCAL_ROOT_DIRECTORY = ".deputydev"


class LocalFiles(Enum):
    CLI_AUTH_TOKEN_FILE = "605b8520-0d06-4b8a-92b0-7ebfec7a9e6d.json"
