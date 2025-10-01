from typing import Any, Dict, List, Optional

from deputydev_core.utils.app_logger import AppLogger
from deputydev_core.utils.config_manager import ConfigManager
from pydantic import BaseModel


class EventManager:
    """Handle event creation operations for QuerySolver."""

    def create_error_event(self, error_message: str) -> BaseModel:
        """
        Create an error event BaseModel for streaming.

        Args:
            error_message: The error message to include

        Returns:
            BaseModel: Error event model
        """

        class StreamErrorEvent(BaseModel):
            type: str = "STREAM_ERROR"
            message: str

        return StreamErrorEvent(message=error_message)

    def create_llm_throttled_error_event(self, ex) -> BaseModel:
        """
        Create a throttled error event BaseModel for streaming.

        Args:
            ex: LLMThrottledError exception

        Returns:
            BaseModel: Throttled error event model
        """

        class LLMThrottledErrorEvent(BaseModel):
            type: str = "STREAM_ERROR"
            status: str = "LLM_THROTTLED"
            provider: Optional[str] = None
            model: Optional[str] = None
            retry_after: Optional[int] = None
            message: str = "This chat is currently being throttled. You can wait, or switch to a different model."
            detail: Optional[str] = None
            region: Optional[str] = None

        return LLMThrottledErrorEvent(
            provider=getattr(ex, "provider", None),
            model=getattr(ex, "model", None),
            retry_after=ex.retry_after,
            detail=ex.detail,
            region=getattr(ex, "region", None),
        )

    async def create_token_limit_error_event(self, ex, query: str) -> BaseModel:
        """
        Create a token limit exceeded error event BaseModel for streaming.

        Args:
            ex: InputTokenLimitExceededError exception
            query: The original query

        Returns:
            BaseModel: Token limit error event model
        """

        # Get available models with higher token limits
        better_models: List[Dict[str, Any]] = []

        try:
            code_gen_models = ConfigManager.configs.get("CODE_GEN_LLM_MODELS", [])
            llm_models_config = ConfigManager.configs.get("LLM_MODELS", {})
            current_model_limit = ex.max_tokens

            for model in code_gen_models:
                model_name = model.get("name")
                if model_name and model_name != ex.model_name and model_name in llm_models_config:
                    model_config = llm_models_config[model_name]
                    model_token_limit = model_config.get("INPUT_TOKENS_LIMIT", 100000)

                    if model_token_limit > current_model_limit:
                        enhanced_model = model.copy()
                        enhanced_model["input_token_limit"] = model_token_limit
                        better_models.append(enhanced_model)

            # Sort by token limit (highest first)
            better_models.sort(key=lambda m: m.get("input_token_limit", 0), reverse=True)

        except Exception as model_error:
            AppLogger.log_error(f"Error fetching better models: {model_error}")

        def get_model_display_name(model_name: str) -> str:
            """Get the display name for a model from the configuration."""
            try:
                chat_models = ConfigManager.configs.get("CODE_GEN_LLM_MODELS", [])
                for model in chat_models:
                    if model.get("name") == model_name:
                        return model.get("display_name", model_name)
                return model_name
            except Exception:
                return model_name

        class TokenLimitErrorEvent(BaseModel):
            type: str = "STREAM_ERROR"
            status: str = "INPUT_TOKEN_LIMIT_EXCEEDED"
            model: str
            current_tokens: int
            max_tokens: int
            query: str
            message: str
            detail: Optional[str]
            better_models: List[Dict[str, Any]]

        return TokenLimitErrorEvent(
            model=ex.model_name,
            current_tokens=ex.current_tokens,
            max_tokens=ex.max_tokens,
            query=query,
            message=f"Your message exceeds the context window supported by {get_model_display_name(ex.model_name)}. Try switching to a model with a higher context window to proceed.",
            detail=ex.detail,
            better_models=better_models,
        )

    def create_completion_event(self) -> BaseModel:
        """Create a query completion event BaseModel for streaming."""

        class QueryCompletionEvent(BaseModel):
            type: str = "QUERY_COMPLETE"

        return QueryCompletionEvent()

    def create_close_event(self) -> BaseModel:
        """Create a stream end close connection event BaseModel for streaming."""

        class StreamEndCloseEvent(BaseModel):
            type: str = "STREAM_END_CLOSE_CONNECTION"

        return StreamEndCloseEvent()

    def create_end_event(self) -> BaseModel:
        """Create a stream end event BaseModel for streaming."""

        class StreamEndEvent(BaseModel):
            type: str = "STREAM_END"

        return StreamEndEvent()