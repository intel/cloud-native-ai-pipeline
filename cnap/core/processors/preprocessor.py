"""
This module provides an object-oriented design for preprocessing the input data
for machine learning models. It implements an abstract base class `Preprocessor`
that serves as a blueprint for custom preprocessing implementations.

The `Preprocessor` class can be extended to create custom preprocessing strategies
for various machine learning tasks, such as resizing and normalizing input data.

These classes can be easily extended or modified to accommodate new preprocessing
strategies and support various machine learning tasks.
"""

from abc import ABC, abstractmethod
import numpy as np

class Preprocessor(ABC):
    """
    Abstract base class for creating custom preprocessors.
    """

    @abstractmethod
    def preprocess(self, frame: np.ndarray) -> np.ndarray:
        """
        Preprocess the input frame before feeding it to the model.

        Args:
            frame: An np.ndarray object representing the input frame.

        Returns: An np.ndarray object representing the preprocessed frame.
        """
        raise NotImplementedError("Subclasses should implement the preprocess() method.")
