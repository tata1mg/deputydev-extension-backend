from deputydev_core.llm_handler.models.dto.message_thread_dto import LLModels

from .claude_3_point_5_sonnet import (
    Claude3Point5PerformanceOptimizationCommentsGenerationPass1Prompt,
)


class Claude3Point7PerformanceOptimizationCommentsGenerationPass1Prompt(
    Claude3Point5PerformanceOptimizationCommentsGenerationPass1Prompt
):
    model_name = LLModels.CLAUDE_3_POINT_7_SONNET
