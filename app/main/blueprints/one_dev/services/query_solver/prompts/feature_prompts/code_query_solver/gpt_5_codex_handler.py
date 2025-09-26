from deputydev_core.llm_handler.models.dto.message_thread_dto import LLModels

from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.gpt_5_handler import (
    Gpt5CustomCodeQuerySolverPromptHandler,
)


class Gpt5CodexCustomCodeQuerySolverPromptHandler(Gpt5CustomCodeQuerySolverPromptHandler):
    model_name = LLModels.OPENROUTER_GPT_5_CODEX
