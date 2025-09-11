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
from deputydev_core.llm_handler.providers.google.prompts.base_prompts.base_gemini_2_point_5_flash_prompt_handler import (
    BaseGemini2Point5FlashPromptHandler,
)
from pydantic import BaseModel

from app.backend_common.dataclasses.dataclasses import PromptCategories
from app.main.blueprints.one_dev.services.query_solver.dataclasses.main import (
    ClassFocusItem,
    CodeSnippetFocusItem,
    DirectoryFocusItem,
    FileFocusItem,
    FunctionFocusItem,
)


class Gemini2Point5FlashIntentSelectorPrompt(BaseGemini2Point5FlashPromptHandler):
    prompt_type = "INTENT_SELECTOR"
    prompt_category = PromptCategories.CODE_GENERATION.value

    def __init__(self, params: Dict[str, Any]) -> None:
        self.params = params

    def get_system_prompt(self) -> str:
        return """
            You are tasked with choosing the best intent from a given set of intents behind a user query. If you do it well, you will be rewarded handsomely.
        """

    def get_prompt(self) -> UserAndSystemMessages:
        system_message = self.get_system_prompt()

        focus_chunks_message = ""

        # focus items
        if self.params.get("focus_items"):
            code_snippet_based_items = [
                item
                for item in self.params["focus_items"]
                if isinstance(item, CodeSnippetFocusItem)
                or isinstance(item, FileFocusItem)
                or isinstance(item, ClassFocusItem)
                or isinstance(item, FunctionFocusItem)
            ]
            if code_snippet_based_items:
                focus_chunks_message = "The user has asked to focus on the following\n"
                for focus_item in code_snippet_based_items:
                    if (
                        isinstance(focus_item, FileFocusItem)
                        or isinstance(focus_item, ClassFocusItem)
                        or isinstance(focus_item, FunctionFocusItem)
                    ):
                        focus_chunks_message += (
                            "<item>"
                            + f"<type>{focus_item.type.value}</type>"
                            + (f"<value>{focus_item.value}</value>" if focus_item.value else "")
                            + (f"<path>{focus_item.path}</path>")
                            + "\n".join([chunk.get_xml() for chunk in focus_item.chunks])
                            + "</item>"
                        )

            directory_items = [item for item in self.params["focus_items"] if isinstance(item, DirectoryFocusItem)]
            if directory_items:
                focus_chunks_message += (
                    "\nThe user has also asked to explore the contents of the following directories:\n"
                )
                for directory_item in directory_items:
                    focus_chunks_message += (
                        "<item>" + "<type>directory</type>" + f"<path>{directory_item.path}</path>" + "<structure>\n"
                    )
                    for entry in directory_item.structure or []:
                        label = "file" if entry.type == "file" else "folder"
                        focus_chunks_message += f"{label}: {entry.name}\n"
                    focus_chunks_message += "</structure></item>"

        # user query
        user_message = f"""
            Here is a query asked on some repository by the user.
            {self.params.get("query")}
        """

        intent_gen_prompt = f"""
        We have the following intents available to choose from:
        {
            "<intents>"
            + "".join(
                f"<intent><name>{intent['name']}</name><description>{intent['description']}</description></intent>"
                for intent in self.params.get("intents", [])
            )
            + "</intents>"
        }

        Also, the last intent used by the user was: {self.params.get("last_agent", "None")}

        If you feel that the current query is a continuation of the last intent, select that intent. If you feel that there is a more specialized intent which is more suited to the user's answer for the last intent, then select it.
        Otherwise, choose the most appropriate intent from the list above. Only choose specialized intents if you're sure that the user's query is related to that intent specifically. For instance, if there are several backend app creation intents with different tech stacks, then select the one which is best suited. Do not select a specialized intent for a generic query. For instance, do not select a node JS backend app creation intent for queries that request a generic backend app creation.
        For intents that are for specialized frameworks, do not select them unless user has mentioned those frameworks in query if not carrying forward the last intent.

        Give the answer in the following format:
        <intent_name>INTENT_NAME_HERE</intent_name>
        """

        return UserAndSystemMessages(
            user_message=(
                (user_message + focus_chunks_message + intent_gen_prompt)
                if focus_chunks_message
                else (user_message + intent_gen_prompt)
            ),
            system_message=system_message,
        )

    @classmethod
    def _parse_text_block(cls, text_block: TextBlockData) -> Dict[str, Any]:
        intent_name: Optional[str] = None
        if "<intent_name>" in text_block.content.text:
            intent_name = text_block.content.text.split("<intent_name>")[1].split("</intent_name>")[0].strip()

        if intent_name:
            return {"intent_name": intent_name}
        raise ValueError("Invalid LLM response format. Intent name not found.")

    @classmethod
    def get_parsed_result(cls, llm_response: NonStreamingResponse) -> List[Dict[str, Any]]:
        final_content: List[Dict[str, Any]] = []

        for content_block in llm_response.content:
            if content_block.type == ContentBlockCategory.TOOL_USE_REQUEST:
                raise NotImplementedError("Tool use request not implemented for this prompt")
            elif content_block.type == ContentBlockCategory.TEXT_BLOCK:
                final_content.append(cls._parse_text_block(content_block))

        return final_content

    @classmethod
    async def get_parsed_streaming_events(cls, llm_response: StreamingResponse) -> AsyncIterator[BaseModel]:
        raise NotImplementedError(f"Streaming events not implemented for {cls.prompt_type}")
