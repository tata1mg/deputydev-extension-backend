from deputydev_core.llm_handler.models.dto.message_thread_dto import LLModels

from .claude_4_sonnet import Claude4CodeMaintainabilityCommentsGenerationPass1Prompt


class Claude4Point5CodeMaintainabilityCommentsGenerationPass1Prompt(
    Claude4CodeMaintainabilityCommentsGenerationPass1Prompt
):
    model_name = LLModels.CLAUDE_4_POINT_5_SONNET
