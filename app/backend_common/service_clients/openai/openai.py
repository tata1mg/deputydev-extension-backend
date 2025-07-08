from typing import Any, AsyncIterator, Dict, Iterable, List, Literal, Optional, Union

import httpx
from deputydev_core.utils.singleton import Singleton
from openai import AsyncOpenAI
from openai._streaming import AsyncStream
from openai.types.chat import ChatCompletion
from openai.types.responses import (
    Response,
    ResponseFormatTextJSONSchemaConfigParam,
    ResponseTextConfigParam,
)
from openai.types.responses.response_stream_event import ResponseStreamEvent
from openai.types.shared_params.response_format_json_object import ResponseFormatJSONObject
from openai.types.shared_params.response_format_text import ResponseFormatText
from torpedo import CONFIG

config = CONFIG.config


class OpenAIServiceClient(metaclass=Singleton):
    def __init__(self) -> None:
        self.__client = AsyncOpenAI(
            api_key=config.get("OPENAI_KEY"),
            timeout=config.get("OPENAI_TIMEOUT"),
            http_client=httpx.AsyncClient(
                timeout=config.get("OPENAI_TIMEOUT"),
                limits=httpx.Limits(
                    max_connections=1000,
                    max_keepalive_connections=100,
                    keepalive_expiry=20,
                ),
            ),
        )

    async def get_llm_non_stream_response(
        self,
        conversation_messages: List[Dict[str, Any]],
        model: str,
        tool_choice: Literal["none", "auto", "required"] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        response_type: Literal["text", "json_object"] = "json_object",
        response_schema: Any = None,
        response_format_name: Any = None,
        response_format_description: Any = None,
        instructions: str = None,
        max_output_tokens: str = None,
    ) -> Response:
        response_type = self._get_response_type(
            response_type=response_type,
            response_schema=response_schema,
            schema_name=response_format_name,
            schema_description=response_format_description,
        )
        response = await self.__client.responses.create(
            input=conversation_messages,
            model=model,
            tool_choice=tool_choice,
            tools=tools,
            stream=False,
            text=response_type,
            parallel_tool_calls=True,
            instructions=instructions,
            max_output_tokens=max_output_tokens,
        )
        # we need both message and output token now to returning full completion message
        return response

    async def get_llm_non_stream_response_chat_api(
        self,
        conversation_messages: List[Dict[str, Any]],
        model: str,
        tool_choice: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        response_type: Literal["text", "json_object"] = "json_object",
    ) -> ChatCompletion:
        # THIS WILL BE DEPRECATED DO NOT USE THIS.
        if response_type == "text":
            response_format = ResponseFormatText(type=response_type)
        else:
            response_format = ResponseFormatJSONObject(type=response_type)
        completion = await self.__client.chat.completions.create(
            model=model,
            response_format=response_format,
            messages=conversation_messages,
            temperature=0.5,
        )

        # we need both message and output token now to returning full completion message
        return completion

    async def create_embedding(  # noqa : ANN201
        self,
        input: Union[str, List[str], Iterable[int], Iterable[Iterable[int]]],
        model: str,
        encoding_format: Literal["float", "base64"],
    ):
        embeddings = await self.__client.embeddings.create(
            input=input, model=model, encoding_format=encoding_format, timeout=2
        )
        return embeddings

    async def get_llm_stream_response(
        self,
        conversation_messages: List[Dict[str, Any]],
        model: str,
        tool_choice: Literal["none", "auto", "required"] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        response_type: Literal["text", "json_object"] = "json_object",
        response_schema: Any = None,
        response_format_name: Any = None,
        response_format_description: Any = None,
        instructions: str = None,
        max_output_tokens: int = None,
    ) -> AsyncIterator[ResponseStreamEvent]:
        response_type = self._get_response_type(
            response_type=response_type,
            response_schema=response_schema,
            schema_name=response_format_name,
            schema_description=response_format_description,
        )
        stream_manager: AsyncStream[ResponseStreamEvent] = await self.__client.responses.create(
            input=conversation_messages,
            model=model,
            tool_choice=tool_choice,
            tools=tools,
            stream=True,
            text=response_type,
            parallel_tool_calls=True,
            instructions=instructions,
            max_output_tokens=max_output_tokens,
        )
        return stream_manager.__stream__()

    def _get_response_type(
        self, response_type: Any, response_schema: Any = None, schema_name: Any = None, schema_description: Any = None
    ) -> ResponseTextConfigParam:
        if response_type == "json_schema":
            return ResponseTextConfigParam(
                format=ResponseFormatTextJSONSchemaConfigParam(
                    name=schema_name,
                    schema=response_schema,
                    type=response_type,
                    description=schema_description,
                )
            )
        elif response_type == "text":
            return ResponseTextConfigParam(format=ResponseFormatText(type=response_type))
        elif response_type == "json_object":
            return ResponseTextConfigParam(format=ResponseFormatJSONObject(type=response_type))
        else:
            raise ValueError("Invalid response type")
