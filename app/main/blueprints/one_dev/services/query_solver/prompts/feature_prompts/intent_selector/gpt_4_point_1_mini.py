import json
from typing import Any, AsyncIterator, Dict, List, Type

from deputydev_core.llm_handler.dataclasses.main import (
    NonStreamingResponse,
    StreamingResponse,
    UserAndSystemMessages,
)
from deputydev_core.llm_handler.models.dto.message_thread_dto import (
    ContentBlockCategory,
)
from deputydev_core.llm_handler.providers.openai.prompts.base_prompts.base_gpt_4_point_1_mini import (
    BaseGpt4Point1MiniPrompt,
)
from deputydev_core.utils.app_logger import AppLogger
from pydantic import BaseModel

from app.backend_common.dataclasses.dataclasses import PromptCategories
from app.main.blueprints.one_dev.services.query_solver.dataclasses.main import (
    ClassFocusItem,
    CodeSnippetFocusItem,
    DirectoryFocusItem,
    FileFocusItem,
    FunctionFocusItem,
)


class SortedAndFilteredIntents(BaseModel):
    intent_name: str


class Gpt4Point1MiniIntentSelectorPrompt(BaseGpt4Point1MiniPrompt):
    prompt_type = "INTENT_SELECTOR"
    prompt_category = PromptCategories.CODE_GENERATION.value

    def __init__(self, params: Dict[str, Any]) -> None:
        self.params = params

    def get_system_prompt(self) -> str:
        return """You are an expert at intent selection. Given a user query and a list of available intents, you need to select the most appropriate intent."""

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
        Here is a query asked on some repository by the user:
        <user_query>{self.params.get("query")}</user_query>
        """
        intents_list = "".join(
            f"- {intent['name']}: {intent['description']}\n" for intent in self.params.get("intents", [])
        )

        intent_gen_prompt = f"""
        We have the following intents available to choose from:
        <intents>
        {intents_list}
        </intents>

        Last intent used by the user: {self.params.get("last_agent", "None")}

        Guidelines to follow:
        - If the user's query continues from the last intent, and is appropriate, select it. If a more specialized intent fits better, prefer that.
        - Choose a specialized intent only if the query directly mentions the relevant specialization (such as a framework or domain).
        - For framework-specific intents, only select if the framework is explicitly referenced in the user's query.
        - Avoid specialized intents for generic or ambiguous queries; instead, use the default intent.
        - When several specializations exist, ensure only the most directly applicable one is selected.

        Respond with this schema:

        Output format:
        Respond ONLY with a JSON object following the structure below (do not include any additional text, explanations, or code blocks):
        {{
          "intent_name": "SELECTED_INTENT_NAME"
        }}
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
    def get_text_format(cls) -> Type[BaseModel]:
        return SortedAndFilteredIntents

    @classmethod
    def get_parsed_result(cls, llm_response: NonStreamingResponse) -> List[Any]:
        final_data: List[Any] = []
        for block in llm_response.content:
            if getattr(block, "type", None) == ContentBlockCategory.TOOL_USE_REQUEST:
                continue
            text = block.content.text.strip()
            try:
                data = json.loads(text)
                if isinstance(data.get("intent_name"), str):
                    final_data.append({"intent_name": data["intent_name"]})
            except json.JSONDecodeError as e:
                AppLogger.log_error(f"Failed to parse JSON from LLM response: {e}, text: {text}")
        return final_data

    @classmethod
    async def get_parsed_streaming_events(cls, llm_response: StreamingResponse) -> AsyncIterator[BaseModel]:
        raise NotImplementedError(f"Streaming events not implemented for {cls.prompt_type}")
