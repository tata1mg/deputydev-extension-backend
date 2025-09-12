from typing import Any, AsyncIterator, Dict, List, Tuple, Union

from deputydev_core.llm_handler.dataclasses.main import (
    NonStreamingResponse,
    StreamingResponse,
    UserAndSystemMessages,
)
from deputydev_core.llm_handler.models.dto.message_thread_dto import MessageData
from deputydev_core.llm_handler.providers.google.prompts.base_prompts.base_gemini_2_point_5_flash_lite_prompt_handler import (
    BaseGemini2Point5FlashLitePromptHandler,
)
from pydantic import BaseModel

from app.backend_common.dataclasses.dataclasses import PromptCategories
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.parsers.gemini.code_block.gemini_2_point_5_flash_lite_code_block_parser import (
    Gemini2Point5FlashLiteCodeBlockParser,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.parsers.gemini.summary.gemini_2_point_5_flash_lite_summary_parser import (
    Gemini2Point5FlashLiteSummaryParser,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.parsers.gemini.thinking.gemini_2_point_5_flash_lite_thinking_parser import (
    Gemini2Point5FlashLiteThinkingParser,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.prompts.gemini.gemini_2_point_5_flash_custom_code_query_solver_prompt import (
    Gemini2Point5FlashCustomCodeQuerySolverPrompt,
)


class Gemini2Point5FlashLiteCustomCodeQuerySolverPromptHandler(BaseGemini2Point5FlashLitePromptHandler):
    prompt_type = "CODE_QUERY_SOLVER"
    prompt_category = PromptCategories.CODE_GENERATION.value
    prompt_class = Gemini2Point5FlashCustomCodeQuerySolverPrompt

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
    def get_parsed_result(cls, llm_response: NonStreamingResponse) -> List[Dict[str, Any]]:
        return cls.prompt_class.get_parsed_result(llm_response)

    @classmethod
    async def get_parsed_streaming_events(cls, llm_response: StreamingResponse) -> AsyncIterator[BaseModel]:
        return cls.parse_streaming_text_block_events(
            events=llm_response.content,
            parsers=[
                Gemini2Point5FlashLiteThinkingParser(),
                Gemini2Point5FlashLiteCodeBlockParser(),
                Gemini2Point5FlashLiteSummaryParser(),
            ],
        )

    @classmethod
    def _get_parsed_custom_blocks(cls, input_string: str) -> List[Dict[str, Any]]:
        return cls.prompt_class._get_parsed_custom_blocks(input_string)

    @classmethod
    def extract_code_block_info(cls, code_block_string: str) -> Dict[str, Union[str, bool, int]]:
        return cls.prompt_class.extract_code_block_info(code_block_string)
