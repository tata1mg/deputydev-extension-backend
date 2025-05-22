from .claude_3_point_5_sonnet import (
    Claude3Point5CodeMaintainabilityCommentsGenerationPass1Prompt,
)
from app.backend_common.models.dto.message_thread_dto import LLModels


class Claude3Point7CodeMaintainabilityCommentsGenerationPass1Prompt(
    Claude3Point5CodeMaintainabilityCommentsGenerationPass1Prompt
):
    model_name = LLModels.CLAUDE_3_POINT_7_SONNET
