from typing import Any, Dict

from deputydev_core.utils.config_manager import ConfigManager

from app.main.blueprints.one_dev.services.config.dataclasses.main import ConfigType
from app.main.blueprints.one_dev.utils.client.dataclasses.main import Clients

ConfigManager.configs


class ConfigFetcher:

    essential_configs = {
        Clients.CLI: {
            "NUMBER_OF_WORKERS": 1,
            "HOST_AND_TIMEOUT": {
                "HOST": "https://api.deputydev.ai",
                # "HOST": "http://localhost:8084",
                "TIMEOUT": ConfigManager.configs["ONE_DEV"]["TIMEOUT"],
            },
            "DD_BROWSER_HOST": ConfigManager.configs["DD_BROWSER_HOST"],
        },
        Clients.VACODE_EXT: {
            "NUMBER_OF_WORKERS": 1,
            "HOST_AND_TIMEOUT": {
                "HOST": "https://api.deputydev.ai",
                # "HOST": "http://localhost:8084",
                "TIMEOUT": ConfigManager.configs["ONE_DEV"]["TIMEOUT"],
            },
            "DD_BROWSER_HOST": ConfigManager.configs["DD_BROWSER_HOST"],
        },
    }

    main_configs = {
        Clients.CLI: {
            "CHUNKING": {
                "CHARACTER_SIZE": ConfigManager.configs["CHUNKING"]["CHARACTER_SIZE"],
                "NUMBER_OF_CHUNKS": ConfigManager.configs["CHUNKING"]["MAX_CHUNKS_CODE_GENERATION"],
                "IS_LLM_RERANKING_ENABLED": ConfigManager.configs["CHUNKING"]["IS_LLM_RERANKING_ENABLED"],
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
        },
        Clients.VACODE_EXT: {
            "CHUNKING": {
                "CHARACTER_SIZE": ConfigManager.configs["CHUNKING"]["CHARACTER_SIZE"],
                "NUMBER_OF_CHUNKS": ConfigManager.configs["CHUNKING"]["MAX_CHUNKS_CODE_GENERATION"],
                "IS_LLM_RERANKING_ENABLED": ConfigManager.configs["CHUNKING"]["IS_LLM_RERANKING_ENABLED"],
            },
            "EMBEDDING": {
                "MODEL": ConfigManager.configs["EMBEDDING"]["MODEL"],
                "TOKEN_LIMIT": ConfigManager.configs["EMBEDDING"]["TOKEN_LIMIT"],
                "MAX_PARALLEL_TASKS": 60,
            },
        },
    }

    @classmethod
    def fetch_configs(cls, client: Clients, config_type: ConfigType) -> Dict[str, Any]:
        if config_type == ConfigType.ESSENTIAL:
            if client in cls.essential_configs:
                return cls.essential_configs[client]
            else:
                raise ValueError(f"Essential configs not found for client {client}")

        if client in cls.main_configs:
            return cls.main_configs[client]
        else:
            raise ValueError(f"Main configs not found for client {client}")
