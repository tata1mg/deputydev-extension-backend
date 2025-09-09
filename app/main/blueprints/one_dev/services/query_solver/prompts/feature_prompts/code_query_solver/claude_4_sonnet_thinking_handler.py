from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.claude_4_sonnet_handler import (
    Claude4CodeQuerySolverPromptHandler,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.prompts.claude.claude_4_thinking_code_query_solver_prompt import (
    Claude4ThinkingCodeQuerySolverPrompt,
)
from deputydev_core.llm_handler.models.dto.message_thread_dto import LLModels


class Claude4ThinkingCodeQuerySolverPromptHandler(Claude4CodeQuerySolverPromptHandler):
    model_name = LLModels.CLAUDE_4_SONNET_THINKING
    prompt_class = Claude4ThinkingCodeQuerySolverPrompt
