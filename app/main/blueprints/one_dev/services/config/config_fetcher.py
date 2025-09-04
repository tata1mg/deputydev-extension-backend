from typing import Any, Dict

from deputydev_core.utils.config_manager import ConfigManager
from deputydev_core.utils.constants.enums import ConfigConsumer

from app.backend_common.service_clients.aws.services.cloudfront import AWSCloudFrontServiceClient
from app.backend_common.utils.dataclasses.main import ClientData
from app.main.blueprints.one_dev.services.config.dataclasses.main import ConfigParams, ConfigType

ConfigManager.configs


class ConfigFetcher:
    essential_configs = {
        ConfigConsumer.CLI: {
            "NUMBER_OF_WORKERS": 1,
            "HOST_AND_TIMEOUT": {
                "HOST": ConfigManager.configs["ONE_DEV"]["HOST"],
                "TIMEOUT": ConfigManager.configs["ONE_DEV"]["TIMEOUT"],
            },
            "BROWSER_HOST": ConfigManager.configs["BROWSER_HOST"],
        },
        ConfigConsumer.VSCODE_EXT: {
            "NUMBER_OF_WORKERS": 1,
            "HOST_AND_TIMEOUT": {
                "HOST": ConfigManager.configs["ONE_DEV"]["HOST"],
                "TIMEOUT": ConfigManager.configs["ONE_DEV"]["TIMEOUT"],
            },
            "BROWSER_HOST": ConfigManager.configs["FAKE_AUTH"]["FAKE_BROWSER_HOST"]
            if ConfigManager.configs["FAKE_AUTH"]["ENABLED"]
            else ConfigManager.configs["BROWSER_HOST"],
            "BINARY": {},
            "DD_HOST_WS": ConfigManager.configs["DD_HOST_WS"],
            "DD_HOST_WS_NON_GATEWAY": ConfigManager.configs["DD_HOST_WS_NON_GATEWAY"],
            "QUERY_SOLVER_ENDPOINT": ConfigManager.configs["QUERY_SOLVER_ENDPOINT"],
            "QUERY_SOLVER_ENDPOINT_NON_GATEWAY": ConfigManager.configs["QUERY_SOLVER_ENDPOINT_NON_GATEWAY"],
            "REVIEW_SOLVER_ENDPOINT": ConfigManager.configs["CODE_REVIEW"]["REVIEW_SOLVER_ENDPOINT"],
            "REVIEW_POST_PROCESS_SOLVER_ENDPOINT": ConfigManager.configs["CODE_REVIEW"]["POST_PROCESS_SOLVER_ENDPOINT"],
            "POLLING_MAX_ATTEMPTS": ConfigManager.configs["POLLING_MAX_ATTEMPTS"],
            "LLM_MODELS": ConfigManager.configs["CODE_GEN_LLM_MODELS"],
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
                "CHARACTER_SIZE": ConfigManager.configs["BINARY"]["CHUNKING"]["CHARACTER_SIZE"],
                "NUMBER_OF_CHUNKS": ConfigManager.configs["BINARY"]["CHUNKING"]["MAX_CHUNKS_CODE_GENERATION"],
                "IS_LLM_RERANKING_ENABLED": ConfigManager.configs["BINARY"]["CHUNKING"]["IS_LLM_RERANKING_ENABLED"],
                "DEFAULT_MAX_CHUNKS_CODE_GENERATION": ConfigManager.configs["CHUNKING"][
                    "DEFAULT_MAX_CHUNKS_CODE_GENERATION"
                ],
            },
            "MCP": {
                "MAX_TOOLS": ConfigManager.configs["BINARY"]["MCP"]["MAX_TOOLS"],
                "SERVER_CONNECTION_TIMEOUT": ConfigManager.configs["BINARY"]["MCP"]["SERVER_CONNECTION_TIMEOUT"],
                "TOOL_RESPONSE_TIMEOUT": ConfigManager.configs["BINARY"]["MCP"]["TOOL_RESPONSE_TIMEOUT"],
                "BUFFER_SIZE": ConfigManager.configs["BINARY"]["MCP"]["BUFFER_SIZE"],
            },
            "EMBEDDING": {
                "MODEL": ConfigManager.configs["BINARY"]["EMBEDDING"]["MODEL"],
                "TOKEN_LIMIT": ConfigManager.configs["BINARY"]["EMBEDDING"]["TOKEN_LIMIT"],
                "MAX_PARALLEL_TASKS": ConfigManager.configs["BINARY"]["EMBEDDING"]["MAX_PARALLEL_TASKS"],
                "MAX_BACKOFF": ConfigManager.configs["BINARY"]["EMBEDDING"]["MAX_BACKOFF"],
            },
            "RELEVANT_CHUNKS": {
                "CHUNKING_ENABLED": ConfigManager.configs["BINARY"]["RELEVANT_CHUNKS"]["CHUNKING_ENABLED"]
            },
            "DEPUTY_DEV": {
                "HOST": ConfigManager.configs["ONE_DEV"]["HOST"],
                "TIMEOUT": ConfigManager.configs["ONE_DEV"]["TIMEOUT"],
                "LIMIT": ConfigManager.configs["ONE_DEV"]["LIMIT"],
                "LIMIT_PER_HOST": ConfigManager.configs["ONE_DEV"]["LIMIT_PER_HOST"],
                "TTL_DNS_CACHE": ConfigManager.configs["ONE_DEV"]["TTL_DNS_CACHE"],
            },
            "WEAVIATE_HOST": "127.0.0.1",
            "WEAVIATE_STARTUP_TIMEOUT": ConfigManager.configs["BINARY"]["WEAVIATE"]["STARTUP_TIMEOUT"],
            "WEAVIATE_STARTUP_HEALTHCHECK_INTERVAL": ConfigManager.configs["BINARY"]["WEAVIATE"][
                "STARTUP_HEALTHCHECK_INTERVAL"
            ],
            "WEAVIATE_HTTP_PORT": ConfigManager.configs["BINARY"]["WEAVIATE"]["HTTP_PORT"],
            "WEAVIATE_GRPC_PORT": ConfigManager.configs["BINARY"]["WEAVIATE"]["GRPC_PORT"],
            "WEAVIATE_VERSION": ConfigManager.configs["BINARY"]["WEAVIATE"]["VERSION"],
            "WEAVIATE_CLIENT_TIMEOUTS": ConfigManager.configs["BINARY"]["WEAVIATE"]["CLIENT_TIMEOUTS"],
            "WEAVIATE_ENV_VARIABLES": ConfigManager.configs["BINARY"]["WEAVIATE"]["ENV_VARIABLES"],
            "NUMBER_OF_WORKERS": ConfigManager.configs["BINARY"]["EMBEDDING"]["NUMBER_OF_WORKERS"],
            "USE_GRACE_PERIOD_FOR_EMBEDDING": ConfigManager.configs["BINARY"]["USE_GRACE_PERIOD_FOR_EMBEDDING"],
            "AUTOCOMPLETE_SEARCH": {
                "PRE_FILTER_LIMIT": ConfigManager.configs["BINARY"]["AUTOCOMPLETE_SEARCH"]["PRE_FILTER_LIMIT"],
                "MAX_RECORDS_TO_RETURN": ConfigManager.configs["BINARY"]["AUTOCOMPLETE_SEARCH"][
                    "MAX_RECORDS_TO_RETURN"
                ],
            },
            "WEAVIATE_BASE_DIR": ConfigManager.configs["BINARY"]["WEAVIATE"]["BASE_DIR"],
            "WEAVIATE_EMBEDDED_DB_PATH": ConfigManager.configs["BINARY"]["WEAVIATE"]["EMBEDDED_DB_PATH"],  # DEPRECATED
            "WEAVIATE_EMBEDDED_DB_BINARY_PATH": ConfigManager.configs["BINARY"]["WEAVIATE"][
                "EMBEDDED_DB_BINARY_PATH"
            ],  # DEPRECATED
            "URL_CONTENT_READER": {
                "MAX_CONTENT_SIZE": ConfigManager.configs["BINARY"]["URL_CONTENT_READER"]["MAX_CONTENT_SIZE"],
                "SUMMARIZE_LARGE_CONTENT": ConfigManager.configs["BINARY"]["URL_CONTENT_READER"][
                    "SUMMARIZE_LARGE_CONTENT"
                ],
                "VALIDATE_CONTENT_UPDATION": ConfigManager.configs["BINARY"]["URL_CONTENT_READER"][
                    "VALIDATE_CONTENT_UPDATION"
                ],
                "BATCH_SIZE": ConfigManager.configs["BINARY"]["URL_CONTENT_READER"]["BATCH_SIZE"],
            },
            "CODE_REVIEW": {
                "MAX_DIFF_SIZE": ConfigManager.configs["BINARY"]["CODE_REVIEW"]["MAX_DIFF_SIZE_IN_CHARS"],
            },
        },
        ConfigConsumer.VSCODE_EXT: {
            "RUDDER": {
                "WRITE_KEY": ConfigManager.configs["RUDDER"]["WRITE_KEY"],
                "WRITE_KEY_ERROR_TRACKING": ConfigManager.configs["RUDDER"]["WRITE_KEY_ERROR_TRACKING"],
                "DATA_PLANE_URL": ConfigManager.configs["RUDDER"]["DATA_PLANE_URL"],
            },
            "VSCODE_IGNORE_FILES": {"EXCLUDE_DIRS": [], "EXCLUDE_EXTS": []},
            "VSCODE_LOGS_RETENTION_DAYS": 7,
            "CHAT_PAYLOAD_MAX_SIZE": ConfigManager.configs["CHAT_PAYLOAD_MAX_SIZE"],
            "CHAT_IMAGE_UPLOAD": {
                "MAX_BYTES": ConfigManager.configs["CHAT_IMAGE_UPLOAD"]["MAX_BYTES"],
                "SUPPORTED_MIMETYPES": ConfigManager.configs["CHAT_IMAGE_UPLOAD"]["SUPPORTED_MIMETYPES"],
                "MAX_FILES": ConfigManager.configs["CHAT_IMAGE_UPLOAD"]["MAX_FILES"],
            },
            "CHAT_FILE_UPLOAD": {
                "MAX_BYTES": ConfigManager.configs["CHAT_FILE_UPLOAD"]["MAX_BYTES"],
                "SUPPORTED_MIMETYPES": ConfigManager.configs["CHAT_FILE_UPLOAD"]["SUPPORTED_MIMETYPES"],
            },
        },
    }

    @classmethod
    async def fetch_configs(
        cls, params: ConfigParams, config_type: ConfigType, client_data: ClientData
    ) -> Dict[str, Any]:
        if config_type == ConfigType.ESSENTIAL:
            if params.consumer in cls.essential_configs:
                config = cls.essential_configs[params.consumer]
                if params.consumer == ConfigConsumer.VSCODE_EXT:
                    await cls.add_vscode_ext_config(
                        config, params=params, config_type=config_type, client_data=client_data
                    )
                return config
            else:
                raise ValueError(f"Essential configs not found for client {params.consumer}")

        if params.consumer in cls.main_configs:
            return cls.main_configs[params.consumer]
        else:
            raise ValueError(f"Main configs not found for {params.consumer}")

    @classmethod
    async def add_vscode_ext_config(
        cls, base_config: Dict[str, Any], params: ConfigParams, config_type: ConfigType, client_data: ClientData
    ) -> None:
        if not params.os or not params.arch:
            raise ValueError("os and arch are required for vscode extension config")
        client_version = client_data.client_version
        arch = params.arch.value
        os = params.os.value
        if config_type == ConfigType.ESSENTIAL:
            original_config = ConfigManager.configs["BINARY"]["FILE"]["latest"][os][arch]
            s3_key = ConfigManager.configs["BINARY"]["FILE"]["latest"][os][arch]["s3_key"]
            if client_version in ConfigManager.configs["BINARY"]["FILE"]:
                original_config = ConfigManager.configs["BINARY"]["FILE"][client_version][os][arch]
                s3_key = ConfigManager.configs["BINARY"]["FILE"][client_version][os][arch]["s3_key"]

            file_config = original_config.copy()
            file_config.pop("s3_key", None)
            if s3_key:
                file_config["download_link"] = await cls._generate_signed_url_for_binary(s3_key)
            base_config["BINARY"] = {
                **file_config,
                "port_range": ConfigManager.configs["BINARY"]["PORT_RANGE"],
                "max_init_retry": ConfigManager.configs["BINARY"]["MAX_INIT_RETRY"],
                "max_alive_retry": ConfigManager.configs["BINARY"]["MAX_ALIVE_RETRY"],
            }

    @classmethod
    async def _generate_signed_url_for_binary(cls, s3_key: str) -> str:
        """
        Generate signed URL for binary download from CloudFront
        """
        distribution_url = ConfigManager.configs["AWS_CLOUDFRONT"]["DISTRIBUTION_URL"]
        key_pair_id = ConfigManager.configs["AWS_CLOUDFRONT"]["KEY_PAIR_ID"]
        private_key_str = ConfigManager.configs["AWS_CLOUDFRONT"]["PRIVATE_KEY"]
        expiry = ConfigManager.configs["AWS_CLOUDFRONT"]["SIGNED_URL_EXPIRY"]

        cloudfront_client = AWSCloudFrontServiceClient(
            distribution_url=distribution_url,
            key_pair_id=key_pair_id,
            private_key_str=private_key_str,
            default_expiry=expiry,
        )

        signed_url = await cloudfront_client.generate_signed_url(s3_key=s3_key, expiry=expiry)
        return signed_url
