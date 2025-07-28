import json
from typing import Any, Dict

from deputydev_core.utils.app_logger import AppLogger
from deputydev_core.utils.config_manager import ConfigManager

from app.backend_common.exception.exception import InputTokenLimitExceededException
from app.backend_common.models.dto.message_thread_dto import LLModels
from app.backend_common.services.llm.base_llm_provider import BaseLLMProvider


class TokenCounter:
    def get_model_token_limit(self, model: LLModels) -> int:
        """Get the input token limit for a specific model."""
        try:
            model_config = ConfigManager.configs["LLM_MODELS"][model.value]
            return model_config["INPUT_TOKENS_LIMIT"]
        except KeyError:
            AppLogger.log_warn(f"Token limit not found for model {model.value}, using default 100000")
            return 100000  # Conservative default

    def payload_content(self, llm_payload: Dict[str, Any], client: BaseLLMProvider) -> str:  # noqa : C901
        """
        Extract the relevant content from LLM payload that will be sent to the LLM for token counting.
        This handles different provider payload structures.
        """
        # Import here to avoid circular import
        from app.backend_common.services.llm.providers.anthropic.llm_provider import Anthropic
        from app.backend_common.services.llm.providers.google.llm_provider import Google
        from app.backend_common.services.llm.providers.openai.llm_provider import OpenAI

        content_parts = []

        try:
            # Handle different provider payload structures
            if isinstance(client, Anthropic):
                # Anthropic structure: system message + messages array
                if "system" in llm_payload:
                    if isinstance(llm_payload["system"], str):
                        content_parts.append(llm_payload["system"])
                    elif isinstance(llm_payload["system"], list):
                        for item in llm_payload["system"]:
                            if isinstance(item, dict) and "text" in item:
                                content_parts.append(item["text"])

                if "messages" in llm_payload:
                    for message in llm_payload["messages"]:
                        if "content" in message:
                            for content in message["content"]:
                                if isinstance(content, dict):
                                    if content.get("type") == "text" and "text" in content:
                                        content_parts.append(content["text"])
                                    elif content.get("type") == "tool_result" and "content" in content:
                                        content_parts.append(str(content["content"]))

            elif isinstance(client, OpenAI):
                # OpenAI structure: system_message + conversation_messages
                if "system_message" in llm_payload and llm_payload["system_message"]:
                    content_parts.append(llm_payload["system_message"])

                if "conversation_messages" in llm_payload:
                    for message in llm_payload["conversation_messages"]:
                        if isinstance(message, dict):
                            if "content" in message:
                                if isinstance(message["content"], str):
                                    content_parts.append(message["content"])
                                elif isinstance(message["content"], list):
                                    for content in message["content"]:
                                        if isinstance(content, dict) and content.get("type") == "input_text":
                                            content_parts.append(content.get("text", ""))
                            elif message.get("type") == "function_call_output" and "output" in message:
                                content_parts.append(str(message["output"]))

            elif isinstance(client, Google):
                # Google structure: system_instruction + contents array
                if "system_instruction" in llm_payload and llm_payload["system_instruction"]:
                    # system_instruction is a Part object, extract text
                    if hasattr(llm_payload["system_instruction"], "text"):
                        content_parts.append(llm_payload["system_instruction"].text)

                if "contents" in llm_payload:
                    for content in llm_payload["contents"]:
                        if hasattr(content, "parts"):
                            for part in content.parts:
                                if hasattr(part, "text") and part.text:
                                    content_parts.append(part.text)
                                elif hasattr(part, "function_response"):
                                    content_parts.append(str(part.function_response))

            # Include tools information for token counting if present
            if "tools" in llm_payload and llm_payload["tools"]:
                try:
                    if isinstance(client, Google):
                        # Handle Google's Tool objects which are not JSON serializable
                        tools_text_parts = []
                        for tool in llm_payload["tools"]:
                            if hasattr(tool, "function_declarations"):
                                for func_decl in tool.function_declarations:
                                    if hasattr(func_decl, "name"):
                                        tools_text_parts.append(func_decl.name)
                                    if hasattr(func_decl, "description"):
                                        tools_text_parts.append(func_decl.description)
                        if tools_text_parts:
                            content_parts.append(" ".join(tools_text_parts))
                    else:
                        # For other providers, try JSON serialization
                        tools_content = json.dumps(llm_payload["tools"])
                        content_parts.append(tools_content)
                except Exception as e:  # noqa : BLE001
                    AppLogger.log_warn(f"Error processing tools for token counting: {e}")
                    # Skip tools if they can't be processed
                    pass

        except Exception as e:  # noqa : BLE001
            AppLogger.log_warn(f"Error extracting payload content for token counting: {e}")
            # Fallback: return a simple placeholder instead of trying to serialize non-serializable objects
            return "Unable to extract content for token counting"

        return "\n".join(content_parts)

    async def validate_payload_token_limit(
        self, llm_payload: Dict[str, Any], client: BaseLLMProvider, llm_model: LLModels
    ) -> None:
        """
        Validate if the LLM payload is within token limits using the provider's get_tokens method.
        Raises InputTokenLimitExceededException if limit is exceeded.
        """
        try:
            # Extract content from payload
            payload_content = self.payload_content(llm_payload, client)

            # Count tokens using the provider's get_tokens method
            token_count = await client.get_tokens(content=payload_content, model=llm_model)

            # Get model token limit
            token_limit = self.get_model_token_limit(llm_model)

            AppLogger.log_debug(f"Token validation for {llm_model.value}: {token_count}/{token_limit} tokens")

            if token_count > token_limit:
                raise InputTokenLimitExceededException(
                    model_name=llm_model.value,
                    current_tokens=token_count,
                    max_tokens=token_limit,
                    detail=f"LLM payload has {token_count} tokens, exceeding limit of {token_limit} for model {llm_model.value}",
                )

        except InputTokenLimitExceededException:
            # Re-raise token limit exceptions as-is
            raise
        except Exception as e:  # noqa : BLE001
            AppLogger.log_error(f"Error validating token limit for model {llm_model.value}: {e}")
            # Don't block the request if token validation fails, just log the error
            pass


# Global instance for reuse
token_counter = TokenCounter()
