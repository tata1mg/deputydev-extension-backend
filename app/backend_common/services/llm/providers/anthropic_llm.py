import json
from typing import Any, AsyncIterator, Dict, List, Optional, Union

from app.backend_common.service_clients.bedrock.bedrock import BedrockServiceClient
from app.backend_common.services.llm.base_llm_provider import BaseLLMProvider
from app.backend_common.services.llm.dataclasses.main import (
    ConversationRole,
    ConversationTools,
    ConversationTurn,
    LLMUsage,
    NonStreamingResponse,
    PromptCacheConfig,
    StreamingContentBlock,
    StreamingResponse,
    UserAndSystemMessages,
)
from app.common.constants.constants import LLMProviders, LLModels
from app.common.utils.app_logger import AppLogger
from app.common.utils.config_manager import ConfigManager
from types_aiobotocore_bedrock_runtime.type_defs import (
    InvokeModelResponseTypeDef,
    InvokeModelWithResponseStreamResponseTypeDef,
)


class Anthropic(BaseLLMProvider):
    def __init__(self):
        super().__init__(LLMProviders.ANTHROPIC.value)
        self.anthropic_client = None
        self.model_settings: Dict[str, Any] = ConfigManager.configs["LLM_MODELS"]["CLAUDE_3_POINT_5_SONNET"]

    def build_llm_payload(
        self,
        prompt: UserAndSystemMessages,
        previous_responses: List[ConversationTurn] = [],
        tools: Optional[ConversationTools] = None,
        cache_config: PromptCacheConfig = PromptCacheConfig(tools=False, system_message=False, conversation=False),
    ) -> Dict[str, Any]:

        # create conversation array
        messages = previous_responses
        user_message = ConversationTurn(role=ConversationRole.USER, content=prompt.user_message)
        messages.append(user_message)

        # create body
        llm_payload = {
            "anthropic_version": self.model_settings["VERSION"],
            "max_tokens": self.model_settings["MAX_TOKENS"],
            "system": prompt.system_message,
            "messages": messages,
        }
        return llm_payload

    async def _get_service_client(self):
        if not self.anthropic_client:
            self.anthropic_client = BedrockServiceClient()
        return self.anthropic_client

    async def _parse_non_streaming_response(self, response: InvokeModelResponseTypeDef) -> NonStreamingResponse:
        body: bytes = await response["body"].read()  # type: ignore
        llm_response = json.loads(body.decode("utf-8"))  # type: ignore

        return NonStreamingResponse(
            content=llm_response["content"][0]["text"],
            tools=[],
            usage=LLMUsage(input=llm_response["usage"]["input_tokens"], output=llm_response["usage"]["output_tokens"]),
        )

    async def _parse_streaming_response(
        self, response: InvokeModelWithResponseStreamResponseTypeDef
    ) -> StreamingResponse:
        usage = LLMUsage(input=0, output=0, cache_read=0, cache_write=0)

        async def stream_content() -> AsyncIterator[StreamingContentBlock]:
            for event in response["body"]:
                chunk = json.loads(event["chunk"]["bytes"])

                # yield content block delta
                if chunk["type"] == "content_block_delta":
                    text = chunk["delta"].get("text", "")
                    yield StreamingContentBlock(type=chunk["type"], content=text)

                # update usage on message start and delta
                if chunk["type"] == "message_start":
                    usage.input += chunk["usage"].get("input_tokens", 0)
                    usage.output += chunk["usage"].get("output_tokens", 0)

                if chunk["type"] == "message_delta":
                    usage.input += chunk["usage"].get("input_tokens", 0)
                    usage.output += chunk["usage"].get("output_tokens", 0)

        return StreamingResponse(content=stream_content(), usage=usage)

    async def call_service_client(
        self, llm_payload: Dict[str, Any], model: LLModels, stream: bool = False, response_type: Optional[str] = None
    ) -> Union[NonStreamingResponse, StreamingResponse]:
        anthropic_client = await self._get_service_client()
        AppLogger.log_debug(json.dumps(llm_payload))
        model_config = self._get_model_config(model)
        if stream is False:
            response = await anthropic_client.get_llm_response(llm_payload=llm_payload, model=model_config["NAME"])
            return await self._parse_non_streaming_response(response)
        else:
            response = await anthropic_client.get_llm_stream_response(
                llm_payload=llm_payload, model=model_config["NAME"]
            )
            return await self._parse_streaming_response(response)
