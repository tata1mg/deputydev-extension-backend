from .claude_3_point_5_sonnet import (
    Claude3Point5CodeCommunicationCommentsGenerationPass1Prompt,
)
from app.backend_common.models.dto.message_thread_dto import LLModels


class Claude3Point7CodeCommunicationCommentsGenerationPass2Prompt(
    Claude3Point5CodeCommunicationCommentsGenerationPass1Prompt
):
    model_name = LLModels.CLAUDE_3_POINT_7_SONNET
