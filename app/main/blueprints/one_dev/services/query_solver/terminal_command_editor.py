from typing import Any, Dict, List

from app.backend_common.services.llm.llm_service_manager import LLMServiceManager
from app.backend_common.utils.dataclasses.main import ClientData
from app.main.blueprints.one_dev.services.query_solver.dataclasses.main import (
    TerminalCommandEditInput,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.dataclasses.main import (
    PromptFeatures,
)
from deputydev_core.llm_handler.dataclasses.main import (
    NonStreamingParsedLLMCallResponse,
)
from deputydev_core.llm_handler.models.dto.message_thread_dto import LLModels

from .prompts.factory import PromptFeatureFactory


class TerminalCommandEditGenerator:
    def _get_response_from_parsed_llm_response(self, parsed_llm_response: List[Dict[str, Any]]) -> Dict[str, Any]:
        terminal_command = None

        for response in parsed_llm_response:
            if response.get("terminal_command"):
                terminal_command = response["terminal_command"]
                break

        return {
            "terminal_command": terminal_command,
        }

    async def get_new_terminal_command(
        self, payload: TerminalCommandEditInput, client_data: ClientData
    ) -> Dict[str, Any]:
        llm_handler = LLMServiceManager().create_llm_handler(
            prompt_factory=PromptFeatureFactory,
            prompt_features=PromptFeatures,
        )

        if payload.query and payload.old_terminal_command:
            llm_response = await llm_handler.start_llm_query(
                session_id=payload.session_id,
                prompt_feature=PromptFeatures.TERMINAL_COMMAND_EDITOR,
                llm_model=LLModels.CLAUDE_4_SONNET,
                prompt_vars={
                    "query": payload.query,
                    "old_terminal_command": payload.old_terminal_command,
                    "os_name": payload.os_name,
                    "shell": payload.shell,
                },
                previous_responses=[],
                stream=False,
            )

            if not isinstance(llm_response, NonStreamingParsedLLMCallResponse):
                raise ValueError("LLM response is not of type NonStreamingParsedLLMCallResponse")

            return self._get_response_from_parsed_llm_response(
                parsed_llm_response=llm_response.parsed_content,
            )

        raise ValueError("query or terminal command must be provided")
