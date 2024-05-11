from typing import Any
from collections import defaultdict


class LexicalSearch:
    """
    Class for performing lexical search using an inverted index.

    Attributes:
        inverted_index (Dict[str, List[int]]): A dictionary representing the inverted index.
        doc_lengths (Dict[int, int]): A dictionary storing the length of each document.
        total_doc_length (float): Total length of all documents.
        k1 (float): Tunable parameter for BM25 ranking formula.
        b (float): Tunable parameter for BM25 ranking formula.
        metadata (Dict[str, Any]): Custom metadata associated with documents.
        tokenizer (Any): Tokenizer object for processing text.
    """

    def __init__(self, tokenizer: Any):
        """
        Initialize the LexicalSearch object.

        Args:
            tokenizer (Any): Tokenizer object for processing text.
        """
        self.inverted_index = defaultdict(list)
        self.doc_lengths = {}
        self.total_doc_length = 0.0
        self.k1 = 1.2
        self.b = 0.75
        self.metadata = {}
        self.tokenizer = tokenizer
