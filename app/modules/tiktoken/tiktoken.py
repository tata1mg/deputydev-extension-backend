import tiktoken


class TikToken:
    """
    Wrapper class for managing text encoding using TikToken library.
    """

    def __init__(self):
        """
        Initialize TikToken class with supported language models.
        """
        llm_models = [
            "gpt-3.5-turbo",
            "gpt-4",
            "gpt-4-1106-preview",
        ]
        self.llm_models = {model: tiktoken.encoding_for_model(model) for model in llm_models}

    def count(self, text: str, model: str = "gpt-3.5-turbo") -> int:
        """
        Count the number of tokens in the input text using the specified language model.

        Args:
            text (str): The input text to be tokenized.
            model (str): The name of the language model to use for tokenization.

        Returns:
            int: The number of tokens in the input text.
        """
        return len(self.llm_models[model].encode(text, disallowed_special=()))

    def truncate_string(self, text: str, model: str = "gpt-4", max_tokens: int = 8192) -> str:
        """
        Truncate the input text to a specified maximum number of tokens using the specified language model.

        Args:
            text (str): The input text to be truncated.
            model (str): The name of the language model to use for tokenization.
            max_tokens (int): The maximum number of tokens to retain in the truncated text.

        Returns:
            str: The truncated text.
        """
        tokens = self.llm_models[model].encode(text)[:max_tokens]
        return self.llm_models[model].decode(tokens)
