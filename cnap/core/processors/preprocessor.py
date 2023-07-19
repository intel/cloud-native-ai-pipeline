"""A Preprocessor module.

This module provides an object-oriented design for preprocessing the input data
for machine learning models.

Classes:
    Preprocessor: An abstract base class for creating custom preprocessoring implementations.
"""

from abc import ABC, abstractmethod
import numpy as np

class Preprocessor(ABC):
    """An abstract base class for creating custom preprocessoring implementations.

    This class serves as a blueprint for subclasses that need to implement
    `preprocess` method for different types of preprocessing tasks.
    """

    @abstractmethod
    def preprocess(self, frame: np.ndarray) -> np.ndarray:
        """Preprocess the input frame before feeding it to the model.

        Args:
            frame (np.ndarray): An np.ndarray object representing the input frame.

        Returns:
            np.ndarray: An np.ndarray object representing the preprocessed frame.

        Raises:
            NotImplementedError: If the subclasses don't implement the method.
        """
        raise NotImplementedError("Subclasses should implement the preprocess() method.")
