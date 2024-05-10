import re
from functools import cached_property
from typing import List


class ContentTokenizer:
    def __init__(self, content: str) -> None:
        """
        Tokenizes content into tokens, bigrams, and trigrams.

        Args:
            content (str): The content to tokenize.
        """
        self.tokens: List[str] = self.__tokenize_call(content)

    @cached_property
    def __tokenize_call(self, content: str) -> List[str]:
        """
        Tokenizes the content into individual tokens.

        Args:
            content (str): The content to tokenize.

        Returns:
            list[str]: List of tokens extracted from the content.
        """

        def check_valid_token(token: str) -> bool:
            return token and len(token) > 1

        matches = re.finditer(r"\b\w+\b", content)
        pos = 0
        valid_tokens: List[str] = []
        variable_pattern = re.compile(r"([A-Z][a-z]+|[a-z]+|[A-Z]+(?=[A-Z]|$))")
        for match in matches:
            text = match.group()
            match.start()
            if "_" in text:  # snakecase
                offset = 0
                for part in text.split("_"):
                    if check_valid_token(part):
                        valid_tokens.append(part.lower())
                        pos += 1
                    offset += len(part) + 1
            elif parts := variable_pattern.findall(text):  # pascal and camelcase
                offset = 0
                for part in parts:
                    if check_valid_token(part):
                        valid_tokens.append(part.lower())
                        pos += 1
                    offset += len(part)
            else:  # everything else
                if check_valid_token(text):
                    valid_tokens.append(text.lower())
                    pos += 1
        return valid_tokens

    @cached_property
    def construct_bigrams(self) -> List[str]:
        """
        Constructs bigrams from the tokens.

        Returns:
            list[str]: List of bigrams.
        """
        res: List[str] = []
        prev_token: str = None
        for token in self.tokens:
            if prev_token:
                joined_token: str = prev_token + "_" + token
                res.append(joined_token)
            prev_token = token
        return res

    @cached_property
    def construct_trigrams(self) -> List[str]:
        """
        Constructs trigrams from the tokens.

        Returns:
            list[str]: List of trigrams.
        """
        res: List[str] = []
        prev_prev_token: str = None
        prev_token: str = None
        for token in self.tokens:
            if prev_token and prev_prev_token:
                joined_token: str = prev_prev_token + "_" + prev_token + "_" + token
                res.append(joined_token)
            prev_prev_token = prev_token
            prev_token = token
        return res

    @cached_property
    def get_all_tokens(self) -> List[str]:
        """
        Retrieves all tokens, bigrams, and trigrams.

        Returns:
            list[str]: List of all tokens, bigrams, and trigrams.
        """
        bigrams: List[str] = self.construct_bigrams
        trigrams: List[str] = self.construct_trigrams
        self.tokens.extend(bigrams)
        self.tokens.extend(trigrams)
        return self.tokens
