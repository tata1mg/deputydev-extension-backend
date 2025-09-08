from typing import Any, AsyncIterator, Dict, List, Tuple, Union

from pydantic import BaseModel

from app.backend_common.dataclasses.dataclasses import PromptCategories
from app.backend_common.models.dto.message_thread_dto import MessageData
from app.backend_common.services.llm.dataclasses.main import (
    NonStreamingResponse,
    StreamingResponse,
    UserAndSystemMessages,
)
from app.backend_common.services.llm.providers.anthropic.prompts.base_prompts.base_claude_3_point_7_sonnet_prompt_handler import (
    BaseClaude3Point7SonnetPromptHandler,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.parsers.claude.code_block.claude_3_point_7_code_block_parser import (
    Claude3Point7CodeBlockParser,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.parsers.claude.summary.claude_3_point_7_summary_parser import (
    Claude3Point7SummaryParser,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.parsers.claude.thinking.claude_3_point_7_thinking_parser import (
    Claude3Point7ThinkingParser,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.prompts.claude.claude_3_point_7_sonnet_custom_code_query_solver_prompt import (
    Claude3Point7CustomCodeQuerySolverPrompt,
)


class Claude3Point7CustomCodeQuerySolverPromptHandler(BaseClaude3Point7SonnetPromptHandler):
    prompt_type = "CODE_QUERY_SOLVER"
    prompt_category = PromptCategories.CODE_GENERATION.value
    prompt_class = Claude3Point7CustomCodeQuerySolverPrompt

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
        return cls.parse_streaming_text_block_events(
            events=llm_response.content,
            parsers=[Claude3Point7ThinkingParser(), Claude3Point7CodeBlockParser(), Claude3Point7SummaryParser()],
        )

    @classmethod
    def _get_parsed_custom_blocks(cls, input_string: str) -> List[Dict[str, Any]]:
        return cls.prompt_class._get_parsed_custom_blocks(input_string)

    @classmethod
    def extract_code_block_info(cls, code_block_string: str) -> Dict[str, Union[str, bool, int]]:
        return cls.prompt_class.extract_code_block_info(code_block_string)
