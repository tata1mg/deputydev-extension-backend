from app.backend_common.models.dto.message_thread_dto import LLModels


class Claude3Point7CodeCommunicationCommentsGenerationPass1Prompt:
    pass


class Claude4CodeCommunicationCommentsGenerationPass2Prompt(
    Claude3Point7CodeCommunicationCommentsGenerationPass1Prompt
):
    model_name = LLModels.CLAUDE_4_SONNET
