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
