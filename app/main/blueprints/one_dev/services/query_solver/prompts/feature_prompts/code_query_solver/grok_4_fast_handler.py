from typing import Any, AsyncIterator, Dict, List, Tuple, Union

from deputydev_core.llm_handler.dataclasses.main import NonStreamingResponse, StreamingResponse, UserAndSystemMessages
from deputydev_core.llm_handler.models.dto.message_thread_dto import LLModels, MessageData
from deputydev_core.llm_handler.providers.openrouter_models.prompts.base_prompts.base_grok_4_fast import (
    BaseGrok4FastPrompt,
)
from pydantic import BaseModel

from app.backend_common.dataclasses.dataclasses import PromptCategories
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.parsers.openrouter_models.code_block.grok_4_fast_code_block_parser import (
    Grok4FastCodeBlockParser,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.parsers.openrouter_models.extended_thinking.grok_4_fast_reasoning_thinking_parser import (
    Grok4FastReasoningThinkingParser,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.prompts.grok.grok_4_fast_custom_code_query_solver_prompt import (
    Grok4FastCustomCodeQuerySolverPrompt,
)


class Grok4FastCustomCodeQuerySolverPromptHandler(BaseGrok4FastPrompt):
    prompt_type = "CODE_QUERY_SOLVER"
    prompt_category = PromptCategories.CODE_GENERATION.value
    model_name = LLModels.OPENROUTER_GROK_4_FAST
    prompt_class = Grok4FastCustomCodeQuerySolverPrompt

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
        handlers = {"extended_thinking_handler": Grok4FastReasoningThinkingParser()}
        return cls.parse_streaming_text_block_events(
            events=llm_response.content,
            parsers=[Grok4FastCodeBlockParser()],
            handlers=handlers,
        )

    @classmethod
    def _get_parsed_custom_blocks(cls, input_string: str) -> List[Dict[str, Any]]:
        return cls.prompt_class._get_parsed_custom_blocks(input_string)

    @classmethod
    def extract_code_block_info(cls, code_block_string: str) -> Dict[str, Union[str, bool, int]]:
        return cls.prompt_class.extract_code_block_info(code_block_string)
