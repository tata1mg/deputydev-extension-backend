from typing import Dict, Type

from deputydev_core.llm_handler.models.dto.message_thread_dto import LLModels
from deputydev_core.llm_handler.prompts.base_feature_prompt_factory import BaseFeaturePromptFactory
from deputydev_core.llm_handler.prompts.base_prompt import BasePrompt
from deputydev_core.llm_handler.prompts.base_prompt_feature_factory import BasePromptFeatureFactory

from .dataclasses.main import PromptFeatures
from .feature_prompts.business_logic_validation_comments_generation_pass_1.factory import (
    BusinessLogicValidationCommentsGenerationPass1PromptFactory,
)
from .feature_prompts.business_logic_validation_comments_generation_pass_2.factory import (
    BusinessLogicValidationCommentsGenerationPass2PromptFactory,
)
from .feature_prompts.code_communication_comments_generation_pass_1.factory import (
    CodeCommunicationCommentsGenerationPass1PromptFactory,
)
from .feature_prompts.code_communication_comments_generation_pass_2.factory import (
    CodeCommunicationCommentsGenerationPass2PromptFactory,
)
from .feature_prompts.code_maintainability_comments_generation_pass_1.factory import (
    CodeMaintainabilityCommentsGenerationPass1PromptFactory,
)
from .feature_prompts.code_maintainability_comments_generation_pass_2.factory import (
    CodeMaintainabilityCommentsGenerationPass2PromptFactory,
)
from .feature_prompts.comment_summarization.factory import (
    CommentSummarizationPromptFactory,
)
from .feature_prompts.comment_validation.factory import CommentValidationPromptFactory
from .feature_prompts.custom_agent_comments_generation.factory import (
    CustomAgentCommentGenerationPromptFactory,
)
from .feature_prompts.error_comments_generation_pass_1.factory import (
    ErrorCommentsGenerationPass1PromptFactory,
)
from .feature_prompts.error_comments_generation_pass_2.factory import (
    ErrorCommentsGenerationPass2PromptFactory,
)
from .feature_prompts.performance_optimization_comments_generation_pass_1.factory import (
    PerformanceOptimizationCommentsGenerationPass1PromptFactory,
)
from .feature_prompts.performance_optimization_comments_generation_pass_2.factory import (
    PerformanceOptimizationCommentsGenerationPass2PromptFactory,
)
from .feature_prompts.pr_summarization.factory import PRSummarizationPromptFactory
from .feature_prompts.security_comments_generation_pass_1.factory import (
    SecurityCommentsGenerationPass1PromptFactory,
)
from .feature_prompts.security_comments_generation_pass_2.factory import (
    SecurityCommentsGenerationPass2PromptFactory,
)


class PromptFeatureFactory(BasePromptFeatureFactory[PromptFeatures]):
    feature_prompt_factory_map: Dict[PromptFeatures, Type[BaseFeaturePromptFactory]] = {
        PromptFeatures.BUSINESS_LOGIC_VALIDATION_COMMENTS_GENERATION_PASS_1: BusinessLogicValidationCommentsGenerationPass1PromptFactory,
        PromptFeatures.BUSINESS_LOGIC_VALIDATION_COMMENTS_GENERATION_PASS_2: BusinessLogicValidationCommentsGenerationPass2PromptFactory,
        PromptFeatures.CODE_COMMUNICATION_COMMENTS_GENERATION_PASS_1: CodeCommunicationCommentsGenerationPass1PromptFactory,
        PromptFeatures.CODE_COMMUNICATION_COMMENTS_GENERATION_PASS_2: CodeCommunicationCommentsGenerationPass2PromptFactory,
        PromptFeatures.CODE_MAINTAINABILITY_COMMENTS_GENERATION_PASS_1: CodeMaintainabilityCommentsGenerationPass1PromptFactory,
        PromptFeatures.CODE_MAINTAINABILITY_COMMENTS_GENERATION_PASS_2: CodeMaintainabilityCommentsGenerationPass2PromptFactory,
        PromptFeatures.ERROR_COMMENTS_GENERATION_PASS_1: ErrorCommentsGenerationPass1PromptFactory,
        PromptFeatures.ERROR_COMMENTS_GENERATION_PASS_2: ErrorCommentsGenerationPass2PromptFactory,
        PromptFeatures.PERFORMANCE_OPTIMIZATION_COMMENTS_GENERATION_PASS_1: PerformanceOptimizationCommentsGenerationPass1PromptFactory,
        PromptFeatures.PERFORMANCE_OPTIMIZATION_COMMENTS_GENERATION_PASS_2: PerformanceOptimizationCommentsGenerationPass2PromptFactory,
        PromptFeatures.SECURITY_COMMENTS_GENERATION_PASS_1: SecurityCommentsGenerationPass1PromptFactory,
        PromptFeatures.SECURITY_COMMENTS_GENERATION_PASS_2: SecurityCommentsGenerationPass2PromptFactory,
        PromptFeatures.CUSTOM_AGENT_COMMENTS_GENERATION: CustomAgentCommentGenerationPromptFactory,
        PromptFeatures.COMMENT_VALIDATION: CommentValidationPromptFactory,
        PromptFeatures.PR_SUMMARIZATION: PRSummarizationPromptFactory,
        PromptFeatures.COMMENT_SUMMARIZATION: CommentSummarizationPromptFactory,
    }

    @classmethod
    def get_prompt(cls, model_name: LLModels, feature: PromptFeatures) -> Type[BasePrompt]:
        feature_prompt_factory = cls.feature_prompt_factory_map.get(feature)
        if not feature_prompt_factory:
            raise ValueError(f"Invalid prompt feature: {feature}")

        prompt_class = feature_prompt_factory.get_prompt(model_name)
        return prompt_class
