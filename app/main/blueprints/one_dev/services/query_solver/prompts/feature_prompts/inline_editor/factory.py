from typing import Type

from app.backend_common.models.dto.message_thread_dto import LLModels
from app.backend_common.services.llm.prompts.base_feature_prompt_factory import (
    BaseFeaturePromptFactory,
)
from app.backend_common.services.llm.prompts.base_prompt import BasePrompt
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.inline_editor.claude_3_point_5_sonnet import (
    Claude3Point5InlineEditorPrompt,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.inline_editor.gemini_2_point_5_pro import (
    Gemini2Point5ProInlineEditorPrompt,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.inline_editor.gpt_4_point_1 import (
    Gpt4Point1InlineEditorPrompt,
)


class InlineEditorPromptFactory(BaseFeaturePromptFactory):
    inline_editor_prompts = {
        LLModels.CLAUDE_3_POINT_5_SONNET: Claude3Point5InlineEditorPrompt,
        LLModels.GEMINI_2_POINT_5_PRO: Gemini2Point5ProInlineEditorPrompt,
        LLModels.GPT_4_POINT_1: Gpt4Point1InlineEditorPrompt,
    }

    @classmethod
    def get_prompt(cls, model_name: LLModels) -> Type[BasePrompt]:
        prompt_class = cls.inline_editor_prompts.get(model_name)
        if not prompt_class:
            raise ValueError(f"Prompt not found for model {model_name}")
        return prompt_class
