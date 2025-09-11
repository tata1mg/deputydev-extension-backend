from typing import Type

from deputydev_core.llm_handler.models.dto.message_thread_dto import LLModels
from deputydev_core.llm_handler.prompts.base_feature_prompt_factory import BaseFeaturePromptFactory
from deputydev_core.llm_handler.prompts.base_prompt import BasePrompt

from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.terminal_command_editor.claude_4_sonnet import (
    Claude4TerminalCommandEditorPrompt,
)


class TerminalCommandEditorPromptFactory(BaseFeaturePromptFactory):
    terminal_command_editor_prompts = {LLModels.CLAUDE_4_SONNET: Claude4TerminalCommandEditorPrompt}

    @classmethod
    def get_prompt(cls, model_name: LLModels) -> Type[BasePrompt]:
        prompt_class = cls.terminal_command_editor_prompts.get(model_name)
        if not prompt_class:
            raise ValueError(f"Prompt not found for model {model_name}")
        return prompt_class
