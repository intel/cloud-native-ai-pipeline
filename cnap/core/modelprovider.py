
"""A Model Provider module.

This module contains the definition of the ModelProvider class, which encapsulates
all relevant information about an model provider in a machine learning pipeline.

A model provider is to get the model information from a server and download the model, in
addition, it also responsible for decrypting an encrypted model.

Classes:
    ModelProvider: An abstract base class for creating custom model provider implementations.
    SimpleModelProvider: A class that implements a simple model provider.
"""

from abc import ABC, abstractmethod

import requests
from core.model import ModelInfo, ModelMetrics, ModelDetails

# Put models to the tmp directory, the tmp directory should be mounted to memory
# from secure concern.
MODEL_DIR = "/tmp/"
# Set the connection timeout to 10s
TIMEOUT = 10

class ModelProvider(ABC):
    """An abstract base class for creating custom model provider implementations.

    This class serves as a blueprint for subclasses that need to implement the `get_model_info`,
    `get_model_data` methods for different inference models.

    Attributes:
        _model_info_url (str): The model info server url.
        _model_id (str): The model ID to retrieve the model informations.
    """

    def __init__(self, model_info_url: str = None, model_id: str = None):
        """Initialize a ModelProvider object."""
        self._model_info_url = model_info_url
        self._model_id = model_id

    @abstractmethod
    def get_model_info(self) -> ModelInfo:
        """Get model info from the model info server.

        The method is to get the model informations from the server.

        Returns:
            ModelInfo: The model informations.

        Raises:
            NotImplementedError: If this method is not implemented by a subclass.
        """
        raise NotImplementedError("Subclasses should implement the get_model_info() method.")

    @abstractmethod
    def get_model_data(self) -> bytes:
        """Get model data.

        The method is to get the model data in bytes.

        Returns:
            bytes: The bytes of the model data.

        Raises:
            NotImplementedError: If this method is not implemented by a subclass.
        """
        raise NotImplementedError("Subclasses should implement the get_model_data() method.")

class SimpleModelProvider(ModelProvider):
    """A concrete class implementing the ModelProvider for a simple model provider.

    This model provider is a simple implementation of the abstract base class `ModelProvider`,
    and the model meta information can be got by simple http server, the response from the server
    is a json format result, here is an example:
    Request:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        req_url = http://{model_info_url}/{model_id}
    Response:
        {
            "id": "c8b019e0-f4d8-4831-8936-f7f64ad99509",
            "framework": "tensorflow",
            "target": "object-detection",
            "url": "http://{model_server_url}/tensorflow/ssdmobilenet_v10.pb.enc",
            "name": "ssdmobilenet",
            "version": "1.0",
            "dtype": "int8",
            "encrypted": true,
            "kbs": "simple_kbs",
            "kbs_url": "https://{key_brocker_server_url}",
            "key_id": "88b3a4b3-ba4b-4e2b-b00e-bc32ca3d56be"
        }
    """
    def __init__(self, model_info_url: str, model_id: str):
        """Initialize a SimpleModelProvider object.

        This constructor initializes a SimpleModelProvider obejct and inherit ModelProvider.

        Attributes:
            _model_data (bytes): The model data in bytes.
        """
        if model_info_url is None:
            raise ValueError(f"Invalid model info url: {model_info_url}")
        if model_id is None:
            raise ValueError(f"Invalid model id: {model_id}")

        super().__init__(model_info_url, model_id)
        self._model_data = None

    def get_model_info(self) -> ModelInfo:
        """Get model information.

        This method is used to get model information from a simple model server, a model `url`
        should be included in the response, and the model will be downloaded and save to MODEL_DIR.

        Returns:
            ModelInfo: The information of the model.

        Raises:
            ConnectionError: If connect to the model info server or model server failed.
            RuntimeError: If the response does not contain model id and model url.
        """
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        req_url = f"{self._model_info_url}/{self._model_id}"
        resp = requests.get(req_url, headers=headers, timeout=TIMEOUT)
        if resp.status_code not in [200]:
            raise ConnectionError(f"Connect model server failed, error code: {resp.status_code}")

        info_data = resp.json()

        if info_data.get("id") is None or info_data.get("url") is None:
            raise RuntimeError("Model info is not valid, id and url should be in the response.")

        # Download model from the `url`
        resp = requests.get(info_data.get("url"), timeout=TIMEOUT)
        if resp.status_code not in [200]:
            raise ConnectionError(f"Download model failed, error code: {resp.status_code}.")

        # Save model to MODEL_DIR
        self._model_data = resp.content
        model_filename = info_data.get("url").split('/')[-1]
        model_filename = model_filename.replace(".enc", "").strip()
        model_path = MODEL_DIR + model_filename

        with open(model_path, "wb") as model_file:
            model_file.write(self._model_data)

        model_detail = ModelDetails(info_data.get("name"), info_data.get("version"),
                                    info_data.get("framework"),info_data.get("target"),
                                    info_data.get("dtype"))
        model_metrics = ModelMetrics(0, 0, 0, 0, 0)
        return ModelInfo(info_data.get("id"), model_path, model_detail, 0, model_metrics)

    def get_model_data(self) -> bytes:
        """Get model data.

        This method is used to get the model data in bytes, it will call get_model_info if the
        model was not downloaded.

        Returns:
            bytes: The model data in bytes.
        """
        if self._model_data is None:
            self.get_model_info()
        return self._model_data

# Model providers mapping, the name will be configured by env INFER_MODEL_PROVIDER
MODEL_PROVIDERS = {
    # name: class
    "simple": SimpleModelProvider
}
