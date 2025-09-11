from typing import Any, AsyncIterator, Dict, List, Optional

from deputydev_core.llm_handler.dataclasses.main import (
    NonStreamingResponse,
    StreamingResponse,
    UserAndSystemMessages,
)
from deputydev_core.llm_handler.models.dto.message_thread_dto import (
    ContentBlockCategory,
    TextBlockData,
)
from deputydev_core.llm_handler.providers.anthropic.prompts.base_prompts.base_claude_4_sonnet_prompt_handler import (
    BaseClaude4SonnetPromptHandler,
)
from pydantic import BaseModel

from app.backend_common.dataclasses.dataclasses import PromptCategories


class Claude4TerminalCommandEditorPrompt(BaseClaude4SonnetPromptHandler):
    prompt_type = "TERMINAL_COMMAND_EDITOR"
    prompt_category = PromptCategories.CODE_GENERATION.value

    def __init__(self, params: Dict[str, Any]) -> None:
        self.params = params

    def get_system_prompt(self) -> str:
        system_message = """
            Rewrite the given terminal command based on the user’s query inside <terminal_command> tags.
            The command should be properly formatted for the user's OS and shell.

        """
        if self.params.get("os_name") and self.params.get("shell"):
            system_message += f"""
            ====

            SYSTEM INFORMATION:

            Operating System: {self.params.get("os_name")}
            Default Shell: {self.params.get("shell")}

            ====
            """
        return system_message

    def get_prompt(self) -> UserAndSystemMessages:
        system_message = self.get_system_prompt()
        user_message = f"""
        User Query: {self.params.get("query")}
        Old Terminal Command: {self.params.get("old_terminal_command")}

        Respond with:
        <terminal_command>
        new command here
        </terminal_command>
        """

        return UserAndSystemMessages(user_message=user_message, system_message=system_message)

    @classmethod
    def _parse_text_block(cls, text_block: TextBlockData) -> Optional[Dict[str, Any]]:
        content = text_block.content.text
        start_tag = "<terminal_command>"
        end_tag = "</terminal_command>"

        if start_tag in content and end_tag in content:
            try:
                command = content.split(start_tag)[1].split(end_tag)[0].strip()
                if command:
                    return {"terminal_command": command}
            except IndexError:
                return None
        return None

    @classmethod
    def get_parsed_result(cls, llm_response: NonStreamingResponse) -> List[Dict[str, Any]]:
        final_content: List[Dict[str, Any]] = []

        for content_block in llm_response.content:
            if content_block.type == ContentBlockCategory.TOOL_USE_REQUEST:
                raise NotImplementedError("Tool use request not implemented for this prompt")
            elif content_block.type == ContentBlockCategory.TEXT_BLOCK:
                parsed_text_block = cls._parse_text_block(content_block)
                if parsed_text_block:
                    final_content.append(parsed_text_block)
        return final_content

    @classmethod
    async def get_parsed_streaming_events(cls, llm_response: StreamingResponse) -> AsyncIterator[BaseModel]:
        raise NotImplementedError(f"Streaming events not implemented for {cls.prompt_type}")
