"""A Inference Service module.

This module contains the implementation of the InferenceService and InferenceTask classes,
which are used to run inference service.

Classes:
    InferenceService: A concrete class implementing the MicroAppBase for inference Service,
      provides a Restful API to run inference.
    InferenceTask: A concrete class of MicroServiceTask for inference task.
"""

import logging
import sys
import time
import signal
import os

from userv.uapp import MicroAppBase, MicroServiceTask
from core.rtdb import RedisDB, RuntimeDatabaseBase
from core.infereng import InferEngineManager, InferenceInfo, InferenceEngine
from core.frame import QATFrameCipher
from core.inferqueue import RedisInferQueueClient, KafkaInferQueueClient, InferQueueClientBase
from core.streambroker import StreamBrokerClientBase, RedisStreamBrokerClient, \
    KafkaStreamBrokerClient
from core.model import Model, ModelMetrics, ModelDetails, ModelInfo
from core.engines.tensorflow_engine import TFModelConfig, TensorFlowEngine

LOG = logging.getLogger(__name__)
CURR_DIR = os.path.dirname(os.path.abspath(__file__))

class InferenceService(MicroAppBase):
    """A concrete class implementing the MicroAppBase for inference Service.

    Inference Service provides a Restful API to run inference.

    The InferenceService class is responsible for connecting to a runtime database,
    loading a model, and setting up the necessary connections to a queue and a broker
    for running inference on incoming data.

    Attributes:
        _db (RuntimeDatabaseBase): The runtime database instance.
        _model_provider (str): The model provider instance.
        _model (Model): The model instance.
        _infer_queue_connector (InferQueueClientBase): The inference queue connector instance.
        _infer_broker_connector (StreamBrokerClientBase): The inference broker connector instance.
        _infer_engine_manager (InferEngineManager): The inference engine manager instance.
        _infer_info (InferenceInfo): The inference information.
        _inference_engine (InferenceEngine): The inference engine instance.
        _is_stopping (bool): A boolean variable that flags if the service is stopping or not.
    """

    def __init__(self):
        """Initialize an InferenceService object."""
        super().__init__()
        self._db = None
        self._model_provider = None
        self._model = None
        self._infer_queue_connector = None
        self._infer_broker_connector = None
        self._infer_engine_manager = None
        self._infer_info = None
        self._inference_engine = None
        self._is_stopping = False

    @property
    def db(self) -> RuntimeDatabaseBase:
        """The runtime database instance.

        If `_db` is None, this function will create a `RuntimeDatabaseBase` object
        and connect to runtime database.

        Returns:
            RuntimeDatabaseBase: An instance of the runtime database.

        Raises:
            NotImplementedError: If the runtime database type is not supported.
            redis.exceptions.ConnectionError: If connection to the Redis server fails.
        """
        if self._db is None:
            runtime_db_type = self.get_env("RUNTIME_DB_TYPE", "redis")
            if runtime_db_type == "redis":
                self._db = RedisDB()
                redis_host = self.get_env("REDIS_HOST", "127.0.0.1")
                redis_port = self.get_env("REDIS_PORT", 6379)
                self._db.connect(redis_host, redis_port)
            else:
                # TODO: support other runtime database type
                LOG.error("Not supported runtime database type: %s", runtime_db_type)
                raise NotImplementedError(f"Runtime database type {runtime_db_type} \
                                          not supported yet.")
        return self._db

    @property
    def model_provider(self) -> str:
        """The model provider instance.

        The method is to instantiate the model provider instance.

        Returns:
            str: The model provider instance. "Not Implemented" in the current version.
        """
        return "Not Implemented"

    @property
    def model(self) -> Model:
        """The model instance."""
        return self._model

    @property
    def infer_queue_connector(self) -> InferQueueClientBase:
        """The inference queue connector instance.

        If `_infer_queue_connector` is None, this function will create a `InferQueueClientBase`
        object and connect to queue server.

        Returns:
            InferQueueClientBase: The inference queue connector instance.

        Raises:
            NotImplementedError: If the runtime database type is not supported.
            redis.exceptions.ConnectionError: If connection to the Redis server fails.
        """
        if self._infer_queue_connector is None:
            queue_type = self.get_env("QUEUE_TYPE", "redis")
            queue_host = self.get_env("QUEUE_HOST", "127.0.0.1")
            if queue_type == "redis":
                self._infer_queue_connector = RedisInferQueueClient()
                queue_port = self.get_env("QUEUE_PORT", 6379)
            elif queue_type == "kafka":
                self._infer_queue_connector = KafkaInferQueueClient()
                queue_port = self.get_env("QUEUE_PORT", 9092)
            else:
                # TODO: support other queue type
                LOG.error("Not supported queue type: %s", queue_type)
                raise NotImplementedError(f"Queue type {queue_type} \
                                          not supported yet.")
            self._infer_queue_connector.connect(queue_host, queue_port)

        return self._infer_queue_connector

    @property
    def infer_broker_connector(self) -> StreamBrokerClientBase:
        """The inference broker connector instance.

        If `_infer_broker_connector` is None, this function will create a `StreamBrokerClientBase`
        object and connect to stream broker server.

        Returns:
            StreamBrokerClientBase: The inference broker connector instance.

        Raises:
            NotImplementedError: If the runtime database type is not supported.
            redis.exceptions.ConnectionError: If connection to the Redis server fails.
        """
        if self._infer_broker_connector is None:
            broker_type = self.get_env("BROKER_TYPE", "redis")
            broker_host = self.get_env("BROKER_HOST", "127.0.0.1")
            if broker_type == "redis":
                self._infer_broker_connector = RedisStreamBrokerClient()
                broker_port = self.get_env("BROKER_PORT", 6379)
            elif broker_type == "kafka":
                self._infer_broker_connector = KafkaStreamBrokerClient()
                broker_port = self.get_env("BROKER_PORT", 9092)
            else:
                # TODO: support other broker type
                LOG.error("Not supported broker type: %s", broker_type)
                raise NotImplementedError(f"Queue type {broker_type} \
                                          not supported yet.")
            self._infer_broker_connector.connect(broker_host, broker_port)

        return self._infer_broker_connector

    @property
    def infer_engine_manager(self) -> InferEngineManager:
        """The inference engine manager instance.

        If `_infer_engine_manager` is None, this function will create a `InferEngineManager` object.

        Returns:
            InferEngineManager: The inference engine manager instance.
        """
        if self._infer_engine_manager is None:
            self._infer_engine_manager = InferEngineManager(self.db)
        return self._infer_engine_manager

    @property
    def infer_info(self) -> InferenceInfo:
        """The inference information.

        If `_infer_info` is None, this function will create a `InferenceInfo` object.

        Returns:
            InferenceInfo: The inference information.
        """
        if self._infer_info is None:
            req_framework = self.get_env("INFER_FRAMEWORK", "tensorflow")
            req_target = self.get_env("INFER_TARGET", "object-detection")
            req_device = self.get_env("INFER_DEVICE", "cpu")
            req_model_name = self.get_env("INFER_MODEL_NAME", "ssdmobilenet")
            req_model_version = self.get_env("INFER_MODEL_VERSION", "1.0")
            # TODO: get model from model provider
            # self._model = self.model_provider.get_model(req_model_name, req_model_version
            #               req_framework, req_target))
            model_metrics = ModelMetrics(0,0,0,0,0)
            model_details = ModelDetails(req_model_name, req_model_version,
                                         req_framework, req_target, 'int8')
            model_info = ModelInfo(model_details, 0, model_metrics)
            self._model = Model(model_info, None)

            self._infer_info = InferenceInfo(req_device, self._model.model_info.id)
        return self._infer_info

    @property
    def inference_engine(self) -> InferenceEngine:
        """The inference engine instance.

        If `_inference_engine` is None, this function will create a `InferenceEngine` object.

        Returns:
            InferenceEngine: The inference engine instance.

        Raises:
            NotImplementedError: If the framework is not supported.
        """
        if self._inference_engine is None:
            if self.model.model_info.details.framework == "tensorflow":
                model_path = os.path.abspath(os.path.join(CURR_DIR, "../../demo/model/model.pb"))
                model_config = TFModelConfig(model_path,
                                             self.model.model_info.details.dtype,
                                             self.model.model_info.details.target,
                                             self.infer_info.device)
                self._inference_engine = TensorFlowEngine(model_config)
            else:
                # TODO: support other framework
                LOG.error("Not supported framework: %s", self.model.model_info.details.framework)
                raise NotImplementedError(f"Framework {self.model.model_info.details.framework} \
                                            not supported yet.")

        return self._inference_engine

    def init(self):
        """Initialization."""

    def cleanup(self):
        """Cleanup.

        Sets the stopping flag and performs necessary cleanup actions.
        """
        self._is_stopping = True
        LOG.debug("cleanup")

        if self.infer_queue_connector:
            self.infer_queue_connector.unregister_infer_queue(self.infer_info.queue_topic)

        if self.infer_engine_manager:
            self.infer_engine_manager.unregister_engine(self.infer_info.id)

    def run(self) -> bool:
        """The main execution function for the service.

        Returns:
            bool: Whether execution was successful or not.
        """
        # verify the model provider
        # self.model_provider.verify()

        while self.infer_info is None:
            time.sleep(1)

        self.infer_queue_connector.register_infer_queue(self.infer_info.queue_topic)

        self.infer_engine_manager.register_engine(self.infer_info,
                                                   self.model.model_info)

        task = InferenceTask(self.inference_engine, self.infer_info,
                             self.infer_queue_connector, self.infer_broker_connector)
        task.start()

        return True

class InferenceTask(MicroServiceTask):
    """A concrete class of MicroServiceTask for inference task.

    Attributes:
        inference_engine (InferenceEngine): The inference engine instance.
        infer_info (InferenceInfo): The inference information.
        infer_queue_connector (InferQueueClientBase): The inference queue connector instance.
        infer_broker_connector (StreamBrokerClientBase): The inference broker connector instance.
    """

    def __init__(self, inference_engine: InferenceEngine,
                 infer_info: InferenceInfo,
                 infer_queue_connector: InferQueueClientBase,
                 infer_broker_connector: StreamBrokerClientBase):
        """Initialize an InferenceTask object.

        Args:
            inference_engine (InferenceEngine): The inference engine instance.
            infer_info (InferenceInfo): The inference information.
            infer_queue_connector (InferQueueClientBase): The inference queue connector instance.
            infer_broker_connector (StreamBrokerClientBase): The inference stream broker connector
              instance.
        """
        MicroServiceTask.__init__(self)
        self.inference_engine = inference_engine
        self.infer_info = infer_info
        self.infer_queue_connector = infer_queue_connector
        self.infer_broker_connector = infer_broker_connector

    def execute(self):
        """The task logic of inference task."""
        while not self.is_task_stopping:

            # 0. Create frame decryption actor
            decrypt_actor = QATFrameCipher()

            # 1. Get a frame from the infer queue
            frame = self.infer_queue_connector.get_frame(
                self.infer_info.queue_topic)
            if frame is None:
                continue
            self.infer_queue_connector.drop(self.infer_info.queue_topic)
            topic = f"result-{frame.pipeline_id}"

            # 2. Decrypt frame
            frame.decrypt(decrypt_actor)

            # 3. decode frame raw data to image
            #image = cv2.imdecode(frame.raw, cv2.IMREAD_COLOR)

            # 4. Run inference on the frame
            prediction, _ = self.inference_engine.predict(frame.raw)
            frame.raw = prediction

            # 5. encode the inference result
            #_, jpeg = cv2.imencode('.jpg', prediction)

            # 6. publish the inference result
            self.infer_broker_connector.publish_frame(topic, frame)

    def stop(self):
        """Stop the inference task."""
        MicroServiceTask.stop(self)

def entry() -> None:
    """The entry of Inference Service."""
    app = InferenceService()

    def signal_handler(num, _):
        """Signal handler.

        Args:
            num (int): The received signal number.
        """
        LOG.error("signal %d", num)
        app.stop()
        sys.exit(1)

    signal_names = ['SIGINT', 'SIGHUP', 'SIGQUIT', 'SIGUSR1', 'SIGTERM']
    for name in signal_names:
        signal.signal(getattr(signal, name), signal_handler)

    app.run_and_wait_task()

if __name__ == "__main__":
    entry()
