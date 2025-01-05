from dataclasses import dataclass

import numpy as np


@dataclass
class BaseClient:
    """
    Base client class for vector normalization.
    """

    def normalize_l2(self, x: np.ndarray) -> np.ndarray:
        """
        Normalize vectors using L2 normalization.

        Args:
            x (np.ndarray): Input vectors.

        Returns:
            np.ndarray: Normalized vectors.
        """
        x = np.array(x)
        if x.ndim == 1:
            norm = np.linalg.norm(x)
            if norm == 0:
                return x
            return x / norm
        else:
            norm = np.linalg.norm(x, 2, axis=1, keepdims=True)
            return np.where(norm == 0, x, x / norm)

    def process_embeddings(self, array: list) -> np.ndarray:
        """
        Convert 2D array to 1D by calculating mean

        Args:
            array (list): Input vectors.

        Returns:
            np.ndarray: Normalized vectors.
        """
        # Since the input is already a 2D numpy array, we don't need to do any conversion
        # We'll just perform the operation to get the desired output

        # we need to combine these embeddings in some way, we take the mean across all embeddings
        processed_array = np.mean(array, axis=0)

        return processed_array
