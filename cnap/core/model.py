"""
This module contains the definition of the ModelInfo class, which encapsulates
all relevant information about an Inference model in a machine learning pipeline.

In addition, ModelInfo instances can be easily serialized to dictionaries
for further processing or storage, by using Python's built-in `dict()` function.
"""

import uuid
from typing import Iterator, Tuple, Any
from datetime import datetime

class ModelMetrics:
    """
    A class that encapsulates the performance metrics of the inference model.
    """
    def __init__(self,
                 accuracy: float,
                 precision: float,
                 recall: float,
                 f1_score: float,
                 loss: float):
        """
        Initialize a ModelMetrics object.

        Args:
            accuracy (float): The accuracy of the model.
            precision (float): The precision of the model.
            recall (float): The recall of the model.
            f1_score (float): The F1 score of the model.
            loss (float): The loss value of the model.
        """
        self._accuracy = accuracy
        self._precision = precision
        self._recall = recall
        self._f1_score = f1_score
        self._loss = loss

    @property
    def accuracy(self) -> float:
        """Get the accuracy of the model."""
        return self._accuracy

    @property
    def precision(self) -> float:
        """Get the precision of the model."""
        return self._precision

    @property
    def recall(self) -> float:
        """Get the recall of the model."""
        return self._recall

    @property
    def f1_score(self) -> float:
        """Get the F1 score of the model."""
        return self._f1_score

    @property
    def loss(self) -> float:
        """Get the loss value of the model."""
        return self._loss

    def __iter__(self) -> Iterator[Tuple[str, Any]]:
        yield 'accuracy', self._accuracy
        yield 'precision', self._precision
        yield 'recall', self._recall
        yield 'f1_score', self._f1_score
        yield 'loss', self._loss

class ModelDetails:
    """
    A class that encapsulates the details of the inference model.
    """
    def __init__(self, name: str, version: str, framework: str, target: str, dtype: str):
        """
        Initialize a ModelDetails object.

        Args:
            name (str): The name of the model.
            version (str): The version of the model.
            framework (str): The framework used to train the model.
            target (str): The target of the model.
            dtype (str): The data type of the model.
        """
        self._name = name
        self._version = version
        self._framework = framework
        self._target = target
        self._dtype = dtype

    @property
    def name(self) -> str:
        """Get the name of the model."""
        return self._name

    @property
    def version(self) -> str:
        """Get the version of the model."""
        return self._version

    @property
    def framework(self) -> str:
        """Get the framework used to train the model."""
        return self._framework

    @property
    def target(self) -> str:
        """Get the target of the model."""
        return self._target

    @property
    def dtype(self) -> str:
        """Get the data type of the model."""
        return self._dtype

    def __iter__(self) -> Iterator[Tuple[str, Any]]:
        yield 'name', self._name
        yield 'version', self._version
        yield 'framework', self._framework
        yield 'target', self._target
        yield 'dtype', self._dtype

class ModelInfo:
    """
    Class for managing information about an Inference model.
    """

    def __init__(self,
                 details: ModelDetails,
                 uploaded_date: datetime,
                 metrics: ModelMetrics):
        """
        Initialize a ModelInfo object.

        Args:
            details (ModelDetails): The details of the model.
            uploaded_date (datetime): The uploaded date of the model.
            metrics (ModelMetrics): The performance metrics of the model.
        """
        self._id = str(uuid.uuid1())
        self._details = details
        self._uploaded_date = uploaded_date
        self._metrics = metrics

    @property
    def id(self) -> str:
        """
        Get the ID of the model (string of UUID).
        """
        return self._id

    @id.setter
    def id(self, new_str: str) -> None:
        """
        Set the ID of the model (string of UUID).
        """
        self._id = str(uuid.UUID(new_str))

    @property
    def details(self) -> ModelDetails:
        """Get the details of the model."""
        return self._details

    @property
    def uploaded_date(self) -> datetime:
        """Get the creation date of the model."""
        return self._uploaded_date

    @property
    def metrics(self) -> ModelMetrics:
        """Get the performance metrics of the model."""
        return self._metrics

    def __iter__(self) -> Iterator[Tuple[str, Any]]:
        yield 'id', self.id
        yield 'details', dict(self._details)
        yield 'uploaded_date', self._uploaded_date
        yield 'metrics', dict(self._metrics)

class Model:
    """
    Class for managing an Inference model.
    """

    def __init__(self, model_info: ModelInfo, model_binary: bytes):
        """
        Initialize a Model object.

        Args:
            model_info (ModelInfo): The information of the model.
            model_binary (bytes): The binary of the model.
        """
        self._model_info = model_info
        self._model_binary = model_binary

    @property
    def model_info(self) -> ModelInfo:
        """Get the information of the model."""
        return self._model_info

    @property
    def model_binary(self) -> bytes:
        """Get the binary of the model."""
        return self._model_binary

    def __iter__(self) -> Iterator[Tuple[str, Any]]:
        yield 'model_info', dict(self._model_info)
        yield 'model_binary', self._model_binary
