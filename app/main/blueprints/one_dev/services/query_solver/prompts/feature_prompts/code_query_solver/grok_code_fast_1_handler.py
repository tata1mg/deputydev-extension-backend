from typing import Any, AsyncIterator, Dict, List, Tuple, Union

from pydantic import BaseModel

from app.backend_common.dataclasses.dataclasses import PromptCategories
from app.backend_common.models.dto.message_thread_dto import LLModels, MessageData
from app.backend_common.services.llm.dataclasses.main import (
    NonStreamingResponse,
    StreamingResponse,
    UserAndSystemMessages,
)
from app.backend_common.services.llm.providers.openrouter_models.prompts.base_prompts.base_grok_code_fast_1 import (
    BaseGrokCodeFast1Prompt,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.parsers.openrouter_models.code_block.grok_code_fast_1_code_block_parser import (
    GrokCodeFast1CodeBlockParser,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.parsers.openrouter_models.extended_thinking.grok_code_fast_1_reasoning_thinking_parser import (
    GrokCodeFast1ReasoningThinkingParser,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.prompts.grok.grok_code_fast_1_custom_code_query_solver_prompt import (
    GrokCodeFast1CustomQuerySolverPrompt,
)


class GrokCodeFast1CustomCodeQuerySolverPromptHandler(BaseGrokCodeFast1Prompt):
    prompt_type = "CODE_QUERY_SOLVER"
    prompt_category = PromptCategories.CODE_GENERATION.value
    model_name = LLModels.OPENROUTER_GROK_CODE_FAST_1
    prompt_class = GrokCodeFast1CustomQuerySolverPrompt

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
        handlers = {"extended_thinking_handler": GrokCodeFast1ReasoningThinkingParser()}
        return cls.parse_streaming_text_block_events(
            events=llm_response.content,
            parsers=[GrokCodeFast1CodeBlockParser()],
            handlers=handlers,
        )

    @classmethod
    def _get_parsed_custom_blocks(cls, input_string: str) -> List[Dict[str, Any]]:
        return cls.prompt_class._get_parsed_custom_blocks(input_string)

    @classmethod
    def extract_code_block_info(cls, code_block_string: str) -> Dict[str, Union[str, bool, int]]:
        return cls.prompt_class.extract_code_block_info(code_block_string)
