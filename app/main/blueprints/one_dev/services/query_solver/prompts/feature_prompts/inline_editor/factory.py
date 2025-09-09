from typing import Type

from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.inline_editor.claude_4_sonnet import (
    Claude4InlineEditorPrompt,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.inline_editor.gemini_2_point_5_pro import (
    Gemini2Point5ProInlineEditorPrompt,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.inline_editor.gpt_4_point_1 import (
    Gpt4Point1InlineEditorPrompt,
)
from deputydev_core.llm_handler.models.dto.message_thread_dto import LLModels
from deputydev_core.llm_handler.prompts.base_feature_prompt_factory import BaseFeaturePromptFactory
from deputydev_core.llm_handler.prompts.base_prompt import BasePrompt


class InlineEditorPromptFactory(BaseFeaturePromptFactory):
    inline_editor_prompts = {
        LLModels.CLAUDE_4_SONNET: Claude4InlineEditorPrompt,
        LLModels.GEMINI_2_POINT_5_PRO: Gemini2Point5ProInlineEditorPrompt,
        LLModels.GPT_4_POINT_1: Gpt4Point1InlineEditorPrompt,
    }

    @classmethod
    def get_prompt(cls, model_name: LLModels) -> Type[BasePrompt]:
        prompt_class = cls.inline_editor_prompts.get(model_name)
        if not prompt_class:
            raise ValueError(f"Prompt not found for model {model_name}")
        return prompt_class
