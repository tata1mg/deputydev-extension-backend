# TODO Remove this file after removing LLM layer
class LLMThrottledError(RuntimeError):
    """
    Raised when the upstream LLM returns a rate-limit / quota error.
    Subclassed for provider-specific throttling.
    """

    def __init__(
        self,
        provider: str,
        model: str | None = None,
        region: str | None = None,
        retry_after: int | None = None,
        detail: str | None = None,
    ) -> None:
        super().__init__(f"{provider} throttled")
        self.provider = provider
        self.model = model
        self.region = region
        self.retry_after = retry_after
        self.detail = detail or ""
