from app.backend_common.models.dto.message_thread_dto import LLModels

from .claude_3_point_7_sonnet import Claude3Point7CodeCommunicationCommentsGenerationPass1Prompt


class Claude4CodeCommunicationCommentsGenerationPass1Prompt(
    Claude3Point7CodeCommunicationCommentsGenerationPass1Prompt
):
    model_name = LLModels.CLAUDE_4_SONNET
