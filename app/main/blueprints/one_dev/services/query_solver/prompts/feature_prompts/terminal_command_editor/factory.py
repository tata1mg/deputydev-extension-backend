from typing import Type

from app.backend_common.models.dto.message_thread_dto import LLModels
from app.backend_common.services.llm.prompts.base_feature_prompt_factory import (
    BaseFeaturePromptFactory,
)
from app.backend_common.services.llm.prompts.base_prompt import BasePrompt
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.terminal_command_editor.claude_3_point_5_sonnet import (
    Claude3Point5TerminalCommandEditorPrompt,
)


class TerminalCommandEditorPromptFactory(BaseFeaturePromptFactory):
    terminal_command_editor_prompts = {LLModels.CLAUDE_3_POINT_5_SONNET: Claude3Point5TerminalCommandEditorPrompt}

    @classmethod
    def get_prompt(cls, model_name: LLModels) -> Type[BasePrompt]:
        prompt_class = cls.terminal_command_editor_prompts.get(model_name)
        if not prompt_class:
            raise ValueError(f"Prompt not found for model {model_name}")
        return prompt_class
