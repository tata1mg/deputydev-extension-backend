from typing import Dict, Type

from deputydev_core.llm_handler.models.dto.message_thread_dto import LLModels
from deputydev_core.llm_handler.prompts.base_feature_prompt_factory import BaseFeaturePromptFactory
from deputydev_core.llm_handler.prompts.base_prompt import BasePrompt
from deputydev_core.llm_handler.prompts.base_prompt_feature_factory import BasePromptFeatureFactory

from app.main.blueprints.deputy_dev.services.code_review.common.prompts.dataclasses.main import PromptFeatures

from .feature_prompts.code_communication_comments_generation.factory import (
    CodeCommunicationCommentsGenerationPromptFactory,
)
from .feature_prompts.code_maintainability_comments_generation.factory import (
    CodeMaintainabilityCommentsGenerationPromptFactory,
)
from .feature_prompts.comment_summarization.factory import (
    CommentSummarizationPromptFactory,
)
from .feature_prompts.comment_validation.factory import (
    CommentValidationPromptFactory,
)
from .feature_prompts.custom_agent_comment_generation.factory import CustomCommentsGenerationPromptFactory
from .feature_prompts.error_comments_generation.factory import ErrorCommentsGenerationPromptFactory
from .feature_prompts.performance_optimization_comments_generation.factory import (
    PerformanceOptimizationCommentsGenerationPromptFactory,
)
from .feature_prompts.security_comments_generation.factory import SecurityCommentsGenerationPromptFactory


class PromptFeatureFactory(BasePromptFeatureFactory[PromptFeatures]):
    feature_prompt_factory_map: Dict[PromptFeatures, Type[BaseFeaturePromptFactory]] = {
        PromptFeatures.COMMENT_SUMMARIZATION: CommentSummarizationPromptFactory,
        PromptFeatures.COMMENT_VALIDATION: CommentValidationPromptFactory,
        PromptFeatures.CODE_COMMUNICATION_COMMENTS_GENERATION: CodeCommunicationCommentsGenerationPromptFactory,
        PromptFeatures.CODE_MAINTAINABILITY_COMMENTS_GENERATION: CodeMaintainabilityCommentsGenerationPromptFactory,
        PromptFeatures.ERROR_COMMENTS_GENERATION: ErrorCommentsGenerationPromptFactory,
        PromptFeatures.PERFORMANCE_OPTIMIZATION_COMMENTS_GENERATION: PerformanceOptimizationCommentsGenerationPromptFactory,
        PromptFeatures.SECURITY_COMMENTS_GENERATION: SecurityCommentsGenerationPromptFactory,
        PromptFeatures.CUSTOM_AGENT_COMMENTS_GENERATION: CustomCommentsGenerationPromptFactory,
    }

    @classmethod
    def get_prompt(cls, model_name: LLModels, feature: PromptFeatures) -> Type[BasePrompt]:
        feature_prompt_factory = cls.feature_prompt_factory_map.get(feature)
        if not feature_prompt_factory:
            raise ValueError(f"Invalid prompt feature: {feature}")

        prompt_class = feature_prompt_factory.get_prompt(model_name)
        return prompt_class
