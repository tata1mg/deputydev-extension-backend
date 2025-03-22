from typing import Any, Dict

from deputydev_core.utils.config_manager import ConfigManager

from app.main.blueprints.one_dev.services.config.dataclasses.main import ConfigType, ConfigParams
from deputydev_core.utils.constants.enums import ConfigConsumer

from app.main.blueprints.one_dev.utils.client.dataclasses.main import ClientData

ConfigManager.configs


class ConfigFetcher:
    essential_configs = {
        ConfigConsumer.CLI: {
            "NUMBER_OF_WORKERS": 1,
            "HOST_AND_TIMEOUT": {
                "HOST": "https://api.deputydev.ai",
                # "HOST": "http://localhost:8084",
                "TIMEOUT": ConfigManager.configs["ONE_DEV"]["TIMEOUT"],
            },
            "DD_BROWSER_HOST": ConfigManager.configs["DD_BROWSER_HOST"],
        },
        ConfigConsumer.VSCODE_EXT: {
            "NUMBER_OF_WORKERS": 1,
            "HOST_AND_TIMEOUT": {
                "HOST": "https://api.deputydev.ai",
                # "HOST": "http://localhost:8084",
                "TIMEOUT": ConfigManager.configs["ONE_DEV"]["TIMEOUT"],
            },
            "DD_BROWSER_HOST": ConfigManager.configs["DD_BROWSER_HOST"],
            "BINARY": {}
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
            "WEAVIATE_SCHEMA_VERSION": 5,
        },
        ConfigConsumer.BINARY: {
            "CHUNKING": {
                "CHARACTER_SIZE": ConfigManager.configs["CHUNKING"]["CHARACTER_SIZE"],
                "NUMBER_OF_CHUNKS": ConfigManager.configs["CHUNKING"]["MAX_CHUNKS_CODE_GENERATION"],
                "IS_LLM_RERANKING_ENABLED": ConfigManager.configs["CHUNKING"]["IS_LLM_RERANKING_ENABLED"],
                "DEFAULT_MAX_CHUNKS_CODE_GENERATION": ConfigManager.configs["CHUNKING"][
                    "DEFAULT_MAX_CHUNKS_CODE_GENERATION"
                ],
            },
            "EMBEDDING": {
                "MODEL": ConfigManager.configs["EMBEDDING"]["MODEL"],
                "TOKEN_LIMIT": ConfigManager.configs["EMBEDDING"]["TOKEN_LIMIT"],
                "MAX_PARALLEL_TASKS": 60,
            },
            "RELEVANT_CHUNKS": {"CHUNKING_ENABLED": False},
            "DEPUTY_DEV": {
                "HOST": ConfigManager.configs["ONE_DEV"]["GATEWAY_HOST"],
                "TIMEOUT": 20,
                "LIMIT": 0,
                "LIMIT_PER_HOST": 0,
                "TTL_DNS_CACHE": 10,
            },
            "WEAVIATE_HOST": "127.0.0.1",
            "WEAVIATE_HTTP_PORT": 8079,
            "WEAVIATE_GRPC_PORT": 50050,
            "WEAVIATE_SCHEMA_VERSION": 5,
            "NUMBER_OF_WORKERS": 1,
            "USE_GRACE_PERIOD_FOR_EMBEDDING": ConfigManager.configs["USE_GRACE_PERIOD_FOR_EMBEDDING"],
        },
        ConfigConsumer.VSCODE_EXT: {
            "RUDDER": {
                "WRITE_KEY": ConfigManager.configs["RUDDER"]["WRITE_KEY"],
                "DATA_PLANE_URL": ConfigManager.configs["RUDDER"]["DATA_PLANE_URL"],
            }
        },
    }

    @classmethod
    def fetch_configs(cls, params: ConfigParams, config_type: ConfigType, client_data: ClientData) -> Dict[str, Any]:
        if config_type == ConfigType.ESSENTIAL:
            if params.consumer in cls.essential_configs:
                config = cls.essential_configs[params.consumer]
                if params.consumer == ConfigConsumer.VSCODE_EXT:
                    cls.add_vscode_ext_config(config, params=params, config_type=config_type, client_data=client_data)
                return config
            else:
                raise ValueError(f"Essential configs not found for client {params.consumer}")

        if params.consumer in cls.main_configs:
            return cls.main_configs[params.consumer]
        else:
            raise ValueError(f"Main configs not found for {params.consumer}")

    @classmethod
    def add_vscode_ext_config(cls, base_config: Dict, params: ConfigParams, config_type: ConfigType,
                              client_data: ClientData):
        client_version = client_data.client_version
        arch = params.arch.value
        os = params.os.value
        if config_type == ConfigType.ESSENTIAL:
            base_config["BINARY"] = {
                **ConfigManager.configs["BINARY"]["FILE"][client_version][os][arch],
                "password": ConfigManager.configs["BINARY"]["PASSWORD"],
                "port_range": ConfigManager.configs["BINARY"]["PORT_RANGE"]
            }
