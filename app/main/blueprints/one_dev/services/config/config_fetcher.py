from typing import Any, Dict

from deputydev_core.utils.config_manager import ConfigManager

from app.main.blueprints.one_dev.services.config.dataclasses.main import ConfigType
from deputydev_core.utils.constants.enums import ConfigConsumer


ConfigManager.configs


class ConfigFetcher:
    essential_configs = {
        ConfigConsumer.CLI: {
            "NUMBER_OF_WORKERS": 1,
            "HOST_AND_TIMEOUT": {
                # "HOST": "https://api.deputydev.ai",
                "HOST": "http://localhost:8084",
                "TIMEOUT": ConfigManager.configs["ONE_DEV"]["TIMEOUT"],
            },
            "DD_BROWSER_HOST": ConfigManager.configs["DD_BROWSER_HOST"],
        },
        ConfigConsumer.VSCODE_EXT: {
            "NUMBER_OF_WORKERS": 1,
            "HOST_AND_TIMEOUT": {
                # "HOST": "https://api.deputydev.ai",
                "HOST": "http://localhost:8084",
                "TIMEOUT": ConfigManager.configs["ONE_DEV"]["TIMEOUT"],
            },
            "DD_BROWSER_HOST": ConfigManager.configs["DD_BROWSER_HOST"],
        },
    }

    main_configs = {
        ConfigConsumer.CLI: {
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
            "WEAVIATE_SCHEMA_VERSION": 5
        },
        ConfigConsumer.BINARY: {
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
            "RELEVANT_CHUNKS": {
                "CHUNKING_ENABLED": False
            },
            "DEPUTY_DEV": {
                "HOST": "http://localhost:8084",
                "TIMEOUT": 20,
                "LIMIT": 0,
                "LIMIT_PER_HOST": 0,
                "TTL_DNS_CACHE": 10
            },
            "WEAVIATE_HOST": "127.0.0.1",
            "WEAVIATE_HTTP_PORT": 8079,
            "WEAVIATE_GRPC_PORT": 50050,
            "WEAVIATE_SCHEMA_VERSION": 5,
            "NUMBER_OF_WORKERS": 1
        },
        ConfigConsumer.VSCODE_EXT: {}
    }

    @classmethod
    def fetch_configs(cls, consumer: ConfigConsumer, config_type: ConfigType) -> Dict[str, Any]:
        if config_type == ConfigType.ESSENTIAL:
            if consumer in cls.essential_configs:
                return cls.essential_configs[consumer]
            else:
                raise ValueError(f"Essential configs not found for client {consumer}")

        if consumer in cls.main_configs:
            return cls.main_configs[consumer]
        else:
            raise ValueError(f"Main configs not found for {consumer}")
