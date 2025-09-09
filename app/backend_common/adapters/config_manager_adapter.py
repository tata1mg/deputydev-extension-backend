from typing import Any, Dict, Optional

from deputydev_core.llm_handler.interfaces.config_interface import ConfigInterface
from deputydev_core.utils.config_manager import ConfigManager


class ConfigManagerAdapter(ConfigInterface):
    """Adapter that wraps your existing ConfigManager"""

    def __init__(self, config_manager: ConfigManager) -> None:
        self.config_manager = config_manager

    # LLMConfigInterface implementation
    def get_llm_max_retry(self) -> int:
        return int(self.config_manager.configs["LLM_MAX_RETRY"])

    def get_llm_models_config(self) -> Dict[str, Any]:
        return self.config_manager.configs["LLM_MODELS"]

    # ProviderConfigInterface implementation
    def get_openai_config(self) -> Optional[Dict[str, Any]]:
        return {
            "OPENAI": {
                "OPENAI_KEY": self.config_manager.configs.get("OPENAI_KEY"),
                "OPENAI_TIMEOUT": self.config_manager.configs.get("OPENAI_TIMEOUT", 60),
            },
            "LLM_MODELS": self.config_manager.configs["LLM_MODELS"],
        }

    def get_gemini_config(self) -> Optional[Dict[str, Any]]:
        return {
            "VERTEX": self.config_manager.configs.get("VERTEX", {}),
            "LLM_MODELS": self.config_manager.configs["LLM_MODELS"],
        }

    def get_anthropic_config(self) -> Optional[Dict[str, Any]]:
        return {
            "AWS": self.config_manager.configs.get("AWS", {}),
            "LLM_MODELS": self.config_manager.configs["LLM_MODELS"],
        }

    def get_openrouter_config(self) -> Optional[Dict[str, Any]]:
        return {
            "OPENROUTER": self.config_manager.configs.get("OPENROUTER", {}),
            "LLM_MODELS": self.config_manager.configs["LLM_MODELS"],
        }

    def get_aws_config(self) -> Optional[Dict[str, Any]]:
        return self.config_manager.configs.get("AWS", {})

    # FileUploadConfigInterface implementation
    def get_s3_config(self) -> Dict[str, Any]:
        return self.config_manager.configs["AWS_S3_BUCKET"]

    def get_file_upload_paths(self) -> Dict[str, str]:
        return {
            "PAYLOAD_FOLDER_PATH": self.config_manager.configs["CHAT_FILE_UPLOAD"]["PAYLOAD_FOLDER_PATH"],
            "IMAGE_FOLDER_PATH": self.config_manager.configs["CHAT_IMAGE_UPLOAD"]["IMAGE_FOLDER_PATH"],
        }
