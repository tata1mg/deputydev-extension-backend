from typing import Any, AsyncIterator, Dict, List, Tuple, Union

from pydantic import BaseModel

from app.backend_common.dataclasses.dataclasses import PromptCategories
from app.backend_common.models.dto.message_thread_dto import MessageData
from app.backend_common.services.llm.dataclasses.main import (
    NonStreamingResponse,
    StreamingResponse,
    UserAndSystemMessages,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.prompts.gemini.gemini_2_point_5_pro_code_query_solver_prompt import Gemini2Point5ProCodeQuerySolverPrompt
from app.backend_common.services.llm.providers.google.prompts.base_prompts.base_gemini_2_point_5_pro_prompt_handler import BaseGemini2Point5ProPromptHandler
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.parsers.gemini.code_block.gemini_2_point_5_flash_code_block_parser import Gemini2Point5FlashCodeBlockParser
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.parsers.gemini.summary.gemini_2_point_5_flash_summary_parser import Gemini2Point5FlashSummaryParser
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.parsers.gemini.thinking.gemini_2_point_5_flash_thinking_parser import Gemini2Point5FlashThinkingParser


class Gemini2Point5ProCodeQuerySolverPromptHandler(BaseGemini2Point5ProPromptHandler):
    prompt_type = "CODE_QUERY_SOLVER"
    prompt_category = PromptCategories.CODE_GENERATION.value
    prompt_class = Gemini2Point5ProCodeQuerySolverPrompt

    def __init__(self, params: Dict[str, Any]):
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
            events=llm_response.content, parsers=[Gemini2Point5FlashThinkingParser(), Gemini2Point5FlashCodeBlockParser(), Gemini2Point5FlashSummaryParser()]
        )

    @classmethod
    def _get_parsed_custom_blocks(cls, input_string: str) -> List[Dict[str, Any]]:
        return cls.prompt_class._get_parsed_custom_blocks(input_string)

    @classmethod
    def extract_code_block_info(cls, code_block_string: str) -> Dict[str, Union[str, bool, int]]:
        return cls.prompt_class.extract_code_block_info(code_block_string)
