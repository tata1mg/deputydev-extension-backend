from app.backend_common.models.dto.message_thread_dto import LLModels
from app.backend_common.services.llm.prompts.base_feature_prompt_factory import (
    BaseFeaturePromptFactory,
)

from .claude_3_point_5_sonnet import Claude3Point5ChunkDescriptionGenerationPrompt


class ChunkDescriptionGenerationPromptFactory(BaseFeaturePromptFactory):
    chunk_description_generation_prompts = {
        LLModels.CLAUDE_3_POINT_5_SONNET: Claude3Point5ChunkDescriptionGenerationPrompt
    }

    @classmethod
    def get_prompt(cls, model_name: LLModels):
        prompt_class = cls.chunk_description_generation_prompts.get(model_name)
        if not prompt_class:
            raise ValueError(f"Prompt not found for model {model_name}")
        return prompt_class
