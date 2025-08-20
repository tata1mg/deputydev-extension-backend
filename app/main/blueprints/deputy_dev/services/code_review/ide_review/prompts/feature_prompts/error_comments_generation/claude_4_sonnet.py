from app.backend_common.models.dto.message_thread_dto import LLModels

from .claude_3_point_7_sonnet import Claude3Point7ErrorCommentsGenerationPrompt


class Claude4ErrorCommentsGenerationPrompt(Claude3Point7ErrorCommentsGenerationPrompt):
    model_name = LLModels.CLAUDE_4_SONNET
