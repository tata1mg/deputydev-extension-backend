from deputydev_core.llm_handler.models.dto.message_thread_dto import LLModels

from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.claude_4_sonnet_handler import (
    Claude4CustomCodeQuerySolverPromptHandler,
)


class Claude4Point5CustomCodeQuerySolverPromptHandler(Claude4CustomCodeQuerySolverPromptHandler):
    model_name = LLModels.CLAUDE_4_POINT_5_SONNET
