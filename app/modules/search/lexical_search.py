from collections import Counter, defaultdict
from math import log
from typing import Any, Dict

from sanic.log import logger


class LexicalSearch:
    """
    Class for performing lexical search using an inverted index.

    Attributes:
        inverted_index: A dictionary representing the inverted index.
        doc_lengths (Dict[int, int]): A dictionary storing the length of each document.
        total_doc_length (float): Total length of all documents.
        k1 (float): Tunable parameter for BM25 ranking formula.
        b (float): Tunable parameter for BM25 ranking formula.
        metadata (Dict[int, Any]): Custom metadata associated with documents.
        tokenizer (Any): Tokenizer object for processing text.
    """

    def __init__(self) -> None:
        """
        Initialize the LexicalSearch object.
        """
        self.inverted_index = defaultdict(list)
        self.doc_lengths: Dict[int, int] = {}
        self.total_doc_length: float = 0.0
        self.k1: float = 1.2
        self.b: float = 0.75
        self.metadata: Dict[int, Any] = {}

    def add_document(self, title: str, token_freq: Counter) -> None:
        """
        Add a document to the inverted index.

        Args:
            title (str): The title of the document.
            token_freq (Counter): The token frequency Counter for the document.
        """
        doc_id = len(self.doc_lengths)
        self.metadata[doc_id] = title
        doc_length = sum(token_freq.values())
        self.doc_lengths[doc_id] = doc_length
        self.total_doc_length += doc_length
        for token, freq in token_freq.items():
            self.inverted_index[token].append((doc_id, freq))

    def bm25(self, doc_id: int, term: str, term_freq: int) -> float:
        """
        Calculate the BM25 score for a term in a document.

        Args:
            doc_id (int): The document ID.
            term (str): The term.
            term_freq (int): The frequency of the term in the document.

        Returns:
            float: The BM25 score.
        """
        num_docs = len(self.doc_lengths)
        idf = log(((num_docs - len(self.inverted_index[term])) + 0.5) / (len(self.inverted_index[term]) + 0.5) + 1.0)
        doc_length = self.doc_lengths[doc_id]
        tf = ((self.k1 + 1) * term_freq) / (
            term_freq + self.k1 * (1 - self.b + self.b * (doc_length / (self.total_doc_length / len(self.doc_lengths))))
        )
        return idf * tf

    def search_document(self, query_tokens: Counter) -> list[tuple[str, float, dict]]:
        """
        Search the index for documents matching the query.

        Args:
            query_tokens (Counter): The token frequency Counter for the query.

        Returns:
            List[Tuple[str, float, Dict]]: A list of tuples containing document title, score, and metadata.
        """
        scores: Dict[int, float] = defaultdict(float)
        for token in query_tokens:
            for doc_id, term_freq in self.inverted_index.get(token, []):
                scores[doc_id] += self.bm25(doc_id, token, term_freq)
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        # Attach metadata to the results
        results_with_metadata = [
            (self.metadata[doc_id], score, self.metadata.get(doc_id, {})) for doc_id, score in sorted_scores
        ]
        return results_with_metadata

    def search_index(self, query_tokens: Counter) -> Dict[int, float]:
        """
        Search the index based on a query.

        This function takes a query_tokens as input and returns a dictionary of document IDs
        and their corresponding scores.

        Args:
            query_tokens (Counter): The token frequency Counter for the query.

        Returns:
            Dict[int, float]: A dictionary containing document IDs and their scores.
        """
        try:
            results_with_metadata = self.search_document(query_tokens)
            # Search the index
            res = {}
            for doc_id, score, _ in results_with_metadata:
                if doc_id not in res:
                    res[doc_id] = score
            # min max normalize scores from 0.5 to 1
            if len(res) == 0:
                max_score = 1
                min_score = 0
            else:
                max_score = max(res.values())
                min_score = min(res.values()) if min(res.values()) < max_score else 0
            res = {k: (v - min_score) / (max_score - min_score) for k, v in res.items()}
            return res
        except Exception as e:
            logger.exception(e)
            return {}
