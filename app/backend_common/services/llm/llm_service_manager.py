# In your app: app/services/llm_service_manager.py
from enum import Enum
from typing import Type, TypeVar

from deputydev_core.llm_handler.core.handler import LLMHandler
from deputydev_core.llm_handler.dataclasses.main import PromptCacheConfig
from deputydev_core.llm_handler.prompts.base_prompt_feature_factory import BasePromptFeatureFactory
from deputydev_core.utils.config_manager import ConfigManager

from app.backend_common.adapters.chat_attachments_repository_adapter import ChatAttachmentsRepositoryAdapter
from app.backend_common.adapters.codegen_task_cache import CodeGenTasksCacheAdapter
from app.backend_common.adapters.config_manager_adapter import ConfigManagerAdapter
from app.backend_common.adapters.message_threads_repository_adapter import MessageThreadsRepositoryAdapter
from app.backend_common.caches.code_gen_tasks_cache import CodeGenTasksCache
from app.backend_common.repository.chat_attachments.repository import ChatAttachmentsRepository
from app.backend_common.repository.message_threads.repository import MessageThreadsRepository

PromptFeatures = TypeVar("PromptFeatures", bound=Enum)


class LLMServiceManager:
    """Factory class to create LLMHandler instances with proper dependencies"""

    def __init__(self) -> None:
        self.config_manager = ConfigManager()
        self.message_threads_repo = MessageThreadsRepository()
        self.chat_attachments_repo = ChatAttachmentsRepository()
        self.code_gen_cache = CodeGenTasksCache()

        self.config_adapter = ConfigManagerAdapter(self.config_manager)
        self.message_threads_adapter = MessageThreadsRepositoryAdapter(self.message_threads_repo)
        self.chat_attachments_adapter = ChatAttachmentsRepositoryAdapter(self.chat_attachments_repo)
        self.cache_adapter = CodeGenTasksCacheAdapter(self.code_gen_cache)

    def create_llm_handler(
        self,
        prompt_factory: Type[BasePromptFeatureFactory[PromptFeatures]],
        prompt_features: Type[PromptFeatures],
        cache_config: PromptCacheConfig = PromptCacheConfig(tools=False, system_message=False, conversation=False),
    ) -> LLMHandler[PromptFeatures]:
        """Create a new LLMHandler instance with all dependencies injected"""
        return LLMHandler(
            prompt_factory=prompt_factory,
            prompt_features=prompt_features,
            message_threads_repo=self.message_threads_adapter,
            chat_attachments_repo=self.chat_attachments_adapter,
            session_cache=self.cache_adapter,
            config=self.config_adapter,
            cache_config=cache_config,
        )
