from typing import Any, Dict

from app.common.utils.config_manager import ConfigManager

ConfigManager.configs


class ConfigFetcher:
    @classmethod
    def fetch_essential_configs_for_cli(cls) -> Dict[str, Any]:
        return {
            "NUMBER_OF_WORKERS": 1,
            "HOST_AND_TIMEOUT": {
                "HOST": "https://api.deputydev.ai",
                # "HOST": "http://localhost:8084",
                "TIMEOUT": ConfigManager.configs["ONE_DEV"]["TIMEOUT"],
            },
            "APP_NAME": "CLI",
            # "DD_BROWSER_HOST": "http://localhost:3000",
            "DD_BROWSER_HOST": "https://deputydev.ai",
        }

    @classmethod
    def fetch_configs_for_cli(cls) -> Dict[str, Any]:
        return {
            "CHUNKING": {
                "CHARACTER_SIZE": ConfigManager.configs["CHUNKING"]["CHARACTER_SIZE"],
                "NUMBER_OF_CHUNKS": ConfigManager.configs["CHUNKING"]["NUMBER_OF_CHUNKS"],
            },
            "EMBEDDING": {
                "MODEL": ConfigManager.configs["EMBEDDING"]["MODEL"],
                "TOKEN_LIMIT": ConfigManager.configs["EMBEDDING"]["TOKEN_LIMIT"],
                "MAX_PARALLEL_TASKS": 60,
            },
            "AUTH_TOKEN_ENV_VAR": "DEPUTYDEV_AUTH_TOKEN",
            "POLLING_INTERVAL": 5,
            "WEAVIATE_HOST": "127.0.0.1",
            "WEAVIATE_HTTP_PORT": 8079,
            "WEAVIATE_GRPC_PORT": 50050,
            "ENABLED_FEATURES": [
                "CODE_GENERATION",
                "DOCS_GENERATION",
                "TEST_GENERATION",
                "TASK_PLANNER",
                "ITERATIVE_CHAT",
                "GENERATE_AND_APPLY_DIFF",
                "PLAN_CODE_GENERATION",
            ],
            "PR_CREATION_ENABLED": True,
            "USE_NEW_CHUNKING": True,
            "USE_LLM_RE_RANKING": False,
            "USE_VECTOR_DB": True,
        }

    @classmethod
    def get_login_config(cls) -> Dict[str, Any]:
        return {
            "DD_BROWSER_HOST": ConfigManager.configs["DD_BROWSER_HOST"],
            "APP_NAME": ConfigManager.configs["APP_NAME"],
        }
