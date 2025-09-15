from deputydev_core.llm_handler.models.dto.message_thread_dto import LLModels

from .claude_3_point_7_sonnet import Claude3Point7CodeMaintainabilityCommentsGenerationPass1Prompt


class Claude4CodeMaintainabilityCommentsGenerationPass1Prompt(
    Claude3Point7CodeMaintainabilityCommentsGenerationPass1Prompt
):
    model_name = LLModels.CLAUDE_4_SONNET
