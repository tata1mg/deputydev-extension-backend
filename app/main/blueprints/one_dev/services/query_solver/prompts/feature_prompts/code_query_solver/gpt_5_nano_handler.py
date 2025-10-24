from typing import Any, AsyncIterator, Dict, List, Tuple, Union

from deputydev_core.llm_handler.dataclasses.main import (
    NonStreamingResponse,
    StreamingResponse,
    UserAndSystemMessages,
)
from deputydev_core.llm_handler.models.dto.message_thread_dto import LLModels, MessageData
from deputydev_core.llm_handler.providers.openrouter_models.prompts.base_prompts.base_gpt_5 import (
    BaseGpt5Prompt,
)
from pydantic import BaseModel

from app.backend_common.dataclasses.dataclasses import PromptCategories
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.parsers.openrouter_models.code_block.gpt_5_code_block_parser import (
    Gpt5CodeBlockParser,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.parsers.openrouter_models.extended_thinking.gpt_5_reasoning_thinking_parser import (
    Gpt5ReasoningThinkingParser,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.parsers.openrouter_models.task_plan.base_task_plan_parser import (
    TaskPlanParser,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.prompts.gpt.gpt_5_nano_custom_code_query_solver_prompt import (
    Gpt5NanoCustomQuerySolverPrompt,
)


class Gpt5NanoCustomCodeQuerySolverPromptHandler(BaseGpt5Prompt):
    prompt_type = "CODE_QUERY_SOLVER"
    prompt_category = PromptCategories.CODE_GENERATION.value
    prompt_class = Gpt5NanoCustomQuerySolverPrompt
    model_name = LLModels.OPENROUTER_GPT_5_NANO

    def __init__(self, params: Dict[str, Any]) -> None:
        self.params = params
        self.prompt = self.prompt_class(params)

    def get_system_prompt(self) -> str:
        return self.prompt.get_system_prompt()

    def get_prompt(self) -> UserAndSystemMessages:
        return self.prompt.get_prompt()

    @classmethod
    def get_parsed_response_blocks(
        cls, response_block: List[MessageData]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        return cls.prompt_class.get_parsed_response_blocks(response_block)

    @classmethod
    def get_parsed_result(cls, llm_response: NonStreamingResponse) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        return cls.prompt_class.get_parsed_result(llm_response)

    @classmethod
    async def get_parsed_streaming_events(cls, llm_response: StreamingResponse) -> AsyncIterator[BaseModel]:
        handlers = {"extended_thinking_handler": Gpt5ReasoningThinkingParser()}
        return cls.parse_streaming_text_block_events(
            events=llm_response.content,
            parsers=[Gpt5CodeBlockParser(), TaskPlanParser()],
            handlers=handlers,
        )

    @classmethod
    def _get_parsed_custom_blocks(cls, input_string: str) -> List[Dict[str, Any]]:
        return cls.prompt_class._get_parsed_custom_blocks(input_string)

    @classmethod
    def extract_code_block_info(cls, code_block_string: str) -> Dict[str, Union[str, bool, int]]:
        return cls.prompt_class.extract_code_block_info(code_block_string)
