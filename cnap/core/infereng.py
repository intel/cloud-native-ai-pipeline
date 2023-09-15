"""A Inference Engine module.

This module contains the definition of InferenceInfo class, which encapsulates the
inference information. It also contains the definition of InferEngineManager class,
which manages inference engines.

In addition, this module provides an object-oriented design for inference engine.

Classes:
    InferenceInfo: A class that encapsulates inference information.
    InferEngineManager: A class to manage inference engines.
    InferenceEngine: An abstract base class for creating custom inference engine implementations.
"""

import logging
import uuid
import time

from typing import Tuple, Iterator, Any, Optional
from abc import ABC, abstractmethod

import numpy as np
from core.rtdb import RuntimeDatabaseBase
from core.model import ModelInfo

LOG = logging.getLogger(__name__)

FRAMEWORK = {
    0:"Tensorflow",
    1:"PyTorch"
}

TARGET = {
    0: "Object-Recognition",
    1: "Face-Detection",
    2: "Body-Detection",
    3: "Pose-Detection"
}

# Default input dimensions
DEFAULT_INPUT_WIDTH = 320
DEFAULT_INPUT_HEIGHT = 240

# Table storing inference engine information
INFER_ENGINE_TABLE = "InferEngine-table"

# Set of valid devices
VALID_DEVICES = {"cpu", "cpu-amx", "gpu", "tpu"}

class InferenceInfo:
    """Inference information class.

    This class encapsulates the inference information, it can be simply encoded and decoded
    by protobuf. A inference information should include enough information for traceability,
    observability, etc.

    Attributes:
        _device (str): The device type for infer engine.
        _model_id (str): The UUID for infer model.
        _id (str): The UUID for Infer Engine Info.
        _queue_topic (str): The queue topic for infer engine.
        _input_size (Tuple[int, int]): The input size tuple required by infer model.
    """

    def __init__(self, device: str, model_id: str) -> None:
        """Initialize an inference engine info object.

        This constructor initializes an inference engine info object with device type and
        model UUID.

        Args:
            device (str): The device type for infer engine.
            model_id (str): The UUID for infer model.

        Raises:
            ValueError: If device type is invalid.
        """
        if device not in VALID_DEVICES:
            raise ValueError(f"Invalid device type: {device}. Valid types are {VALID_DEVICES}.")
        self._device = device
        self._model_id = model_id
        self._id = None
        self._queue_topic = None
        self._input_size = (
            DEFAULT_INPUT_WIDTH, DEFAULT_INPUT_HEIGHT)

    @property
    def id(self) -> str:
        """str: The UUID for Infer Engine Info."""
        if self._id is None:
            self._id = uuid.uuid1()
        return str(self._id)

    @id.setter
    def id(self, new_str: str) -> None:
        """Set UUID for Infer Engine Info."""
        self._id = uuid.UUID(new_str)

    @property
    def input_size(self) -> Tuple[int, int]:
        """Tuple[int, int]: The input size tuple required by infer model."""
        return self._input_size

    @property
    def device(self) -> str:
        """str: The device type for infer engine."""
        return self._device

    @property
    def model_id(self) -> str:
        """str: The UUID for infer model."""
        return self._model_id

    @property
    def queue_topic(self) -> str:
        """str: The queue topic for infer engine."""
        if self._queue_topic is None:
            self._queue_topic = f"origin-{self.model_id}-{self.device}"
        return self._queue_topic

    @queue_topic.setter
    def queue_topic(self, new_queue_topic: str) -> None:
        """Set queue topic for infer engine."""
        self._queue_topic = new_queue_topic

    def __iter__(self) -> Iterator[Tuple[str, Any]]:
        """The Iterator for InferenceInfo class."""
        yield 'id', self.id
        yield 'device', self.device
        yield 'model_id', self.model_id

class InferEngineManager:
    """The class to manage inference engines.

    This class is the class that manages inference engines, it provides `register_engine`
    and `unregister_engine` methods to register and unregister inference engines, and provides
    `search_engine` method to search available engines.

    Attributes:
        _db (RuntimeDatabaseBase): The RuntimeDatabaseBase object for InferEngineManager to use.
    """

    _instance = None

    def __init__(self, db: RuntimeDatabaseBase) -> None:
        """Initialize a InferEngineManager object.

        This constructor initializes a InferEngineManager object with a RuntimeDatabaseBase object.

        Args:
            db: The RuntimeDatabaseBase object for InferEngineManager to use.
        """
        self._db = db

    def search_engine(self, framework: str, target: str, device: str,
                      model_name: str, model_version: str) -> Optional[InferenceInfo]:
        """Search inference engine.

        This method is uesd to search the engine according to the framework and target requested,
        return the InferenceInfo include the UUID of infer engine.

        Args:
            framework (str): Framework of the model
            target (str): Target of the model
            device (str): Device type for infer engine
            model_name (str): Name of the model
            model_version (str): Version of the model

        Returns:
            InferenceInfo: An InferenceInfo object if engine is found, None otherwise.
        """
        # Get all available engines from database
        engine_dicts = self._db.get_all_table_objects_dict(INFER_ENGINE_TABLE)

        # Find the first engine that matches the desired framework and target\
        try:
            matching_engine_id, matching_engine_dict = next(
                ((key, engine_dict) for key, engine_dict in engine_dicts.items()
                if engine_dict['model']['details']['framework'] == framework
                and engine_dict['model']['details']['target'] == target
                and engine_dict['model']['details']['name'] == model_name
                and engine_dict['model']['details']['version'] == model_version
                and engine_dict['infer']['device'] == device
                ),
                (None, None))
        except KeyError as e:
            logging.error("Missing key in dictionary: %s", e)
            matching_engine_id, matching_engine_dict = None, None

        if matching_engine_dict is None or matching_engine_id is None:
            LOG.error("No matching engine found for framework for the request")
            return None

        # Convert matching engine dict to InferenceInfo object and return
        matching_engine_info = InferenceInfo(
            matching_engine_dict['infer']['device'],
            matching_engine_dict['model']['id'])
        matching_engine_info.id = matching_engine_id

        return matching_engine_info

    def register_engine(self, infer_info: InferenceInfo, model_info: ModelInfo) -> None:
        """Register the infer engine to database.

        This method is used to register the infer engine to database.

        Args:
            infer_info (InferenceInfo): The InferenceInfo object to register.
            model_info (ModelInfo): The ModelInfo object to register.
        """
        data = {
        "infer": dict(infer_info),
        "model": dict(model_info)
        }

        self._db.save_table_object_dict(
            INFER_ENGINE_TABLE,
            infer_info.id,
            data
            )

    def unregister_engine(self, infer_info_id: str) -> None:
        """Unregister the infer engine from database.

        This method is used to unregister the infer engine from database.

        Args:
            infer_info_id (str): The UUID of Infer Engine Info to unregister.
        """
        self._db.del_table_object(INFER_ENGINE_TABLE, infer_info_id)

class InferenceEngine(ABC):
    """An abstract base class for creating custom inference engine implementations.

    This class serves as a blueprint for subclasses that need to implement the `verify`,
    `preprocess`, `postprocess`, `_predict` methods for different inference frameworks.
    """

    @abstractmethod
    def verify(self) -> bool: # pragma: no cover
        """Checks if the model is valid for inference.

        The method is to check if the model is valid for inference.

        Returns:
            bool: True if the model is valid, otherwise False.

        Raises:
            NotImplementedError: If this method is not implemented by a subclass.
        """
        raise NotImplementedError("Subclasses should implement the verify() method.")

    @abstractmethod
    def preprocess(self, frame: np.ndarray) -> np.ndarray: # pragma: no cover
        """Preprocesses the input data.

        The method is to preprocess the input data before feeding it to the model.

        Args:
            frame (np.ndarray): The input data to preprocess.

        Returns:
            np.ndarray: The preprocessed input data.

        Raises:
            NotImplementedError: If this method is not implemented by a subclass.
        """
        raise NotImplementedError("Subclasses should implement the preprocess() method.")

    def predict(self, frame: np.ndarray) -> Tuple[np.ndarray, float]:
        """Performs inference using the loaded model and input data, and measures the latency.

        The method is to perform inference using the loaded model and input data, and measures
        the latency.

        Args:
            frame (np.ndarray): The input data to use for inference.

        Returns:
            Tuple[np.ndarray, float]: The postprocessed result and the latency in seconds.
        """
        preprocessed_frame = self.preprocess(frame)

        start_time = time.time()
        prediction = self._predict(preprocessed_frame)
        latency = time.time() - start_time

        postprocessed_result = self.postprocess(frame, prediction)

        return postprocessed_result, latency

    @abstractmethod
    def postprocess(self, frame: np.ndarray, outputs: dict) -> np.ndarray: # pragma: no cover
        """Postprocesses the output from the inference process.

        The method is to postprocess the output from the inference process.

        Args:
            frame (np.ndarray): The input frame.
            outputs (dict): The output result from the inference process.

        Returns:
            np.ndarray: The postprocessed result.

        Raises:
            NotImplementedError: If this method is not implemented by a subclass.
        """
        raise NotImplementedError("Subclasses should implement the postprocess() method.")

    @abstractmethod
    def _predict(self, preprocessed_frame: np.ndarray) -> dict: # pragma: no cover
        """Performs inference using the loaded model and preprocessed input data.

        The method is to perform inference using the loaded model and preprocessed input data.

        Args:
            preprocessed_frame (np.ndarray): The preprocessed input data to use for inference.

        Returns:
            dict: The output result of the inference.

        Raises:
            NotImplementedError: If this method is not implemented by a subclass.
        """
        raise NotImplementedError("Subclasses should implement the _predict() method.")
