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

from prometheus_client import start_http_server

from core.rtdb import RedisDB, RuntimeDatabaseBase
from core.infereng import InferEngineManager, InferenceInfo, InferenceEngine
from core.frame import QATFrameCipher, Frame
from core.inferqueue import RedisInferQueueClient, KafkaInferQueueClient, InferQueueClientBase
from core.streambroker import StreamBrokerClientBase, RedisStreamBrokerClient, \
    KafkaStreamBrokerClient
from core.model import Model, ModelMetrics, ModelDetails, ModelInfo
from core.engines.tensorflow_engine import TFModelConfig, TensorFlowEngine
from core.metrics import MetricsManager, MetricType
from core.pipeline import PipelineManager
from core.crypto.qat import QATZip
from core.crypto.zip import CPUZip, ZipBase
from userv.uapp import MicroAppBase, MicroServiceTask


LOG = logging.getLogger(__name__)
CURR_DIR = os.path.dirname(os.path.abspath(__file__))

metrics_manager = MetricsManager()
metrics_manager.create_metric(MetricType.GAUGE, 'infer_fps', 'Inferred frames per second')
metrics_manager.create_metric(MetricType.GAUGE, 'drop_fps', 'Dropped frames per second')
metrics_manager.create_metric(MetricType.HISTOGRAM, 'streaming_to_inference_latency', 'Latency \
between frame generation in streaming service and inference completion in inference service')

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
        _pipeline_manager (PipelineManager): The pipeline manager instance.
        _zip_tool (ZipBase): The zip tool instance.
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
        self._pipeline_manager = None
        self._zip_tool = None

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

    @property
    def pipeline_manager(self) -> PipelineManager:
        """The pipeline manager instance.

        If `_pipeline_manager` is None, this function will create a `PipelineManager` object.

        Returns:
            PipelineManager: An instance of PipelineManager class.
        """
        if self._pipeline_manager is None:
            self._pipeline_manager = PipelineManager(self.db)
        return self._pipeline_manager

    @property
    def zip_tool(self) -> ZipBase:
        """The zip tool instance.
        
        If `_zip_tool` is None, this function will create a `ZipBase` object.
        
        Returns:
            ZipBase: The zip tool instance.

        Raises:
            NotImplementedError: If the runtime database type is not supported.
            qat.exceptions.RuntimeError: If QAT initialize fails.
        """
        if self._zip_tool is None:
            zip_enable = self.get_env("ZIP_ENABLE","false")
            if zip_enable == "true":
                zip_tool = self.get_env("ZIP_TOOL","CPU")
                if zip_tool == "QAT":
                    self._zip_tool  = QATZip()
                elif zip_tool == "CPU":
                    self._zip_tool = CPUZip()
                else:
                    LOG.error("Not support zip tools type: %s", zip_tool)
                    raise NotImplementedError(f"zip tools type {zip_tool} \
                                          not supported yet.")
            else:
                LOG.warning("The ZIP_ENABLE is false, confirm if zip is required.")
        return self._zip_tool

    def init(self):
        """Initialization."""

    def cleanup(self):
        """Cleanup.

        Sets the stopping flag and performs necessary cleanup actions.
        """
        self._is_stopping = True
        LOG.debug("cleanup")

        if self.pipeline_manager:
            self.pipeline_manager.clean_infer_engine(self.infer_info.id)

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
                             self.infer_queue_connector, self.infer_broker_connector,
                             self.pipeline_manager, self.get_env("FPS_TIME_WINDOW", 60.0),
                             self.zip_tool)
        task.start()
        start_http_server(8000)

        return True

class InferenceTask(MicroServiceTask):
    """A concrete class of MicroServiceTask for inference task.

    Attributes:
        inference_engine (InferenceEngine): The inference engine instance.
        infer_info (InferenceInfo): The inference information.
        infer_queue_connector (InferQueueClientBase): The inference queue connector instance.
        infer_broker_connector (StreamBrokerClientBase): The inference broker connector instance.
        pipeline_manager (PipelineManager): The pipeline manager instance.
        infer_frame_count (dict): A dictonary that saves the inference frame counts for every
          pipeline.
        drop_frame_count (dict): A dictonary that saves the drop frame counts for every pipeline.
        infer_frame_count_sum (int): The sum of inference frame counts.
        drop_frame_count_sum (int): The sum of drop frame counts.
        infer_start_time (float): The start time of inference/drop frame counting.
        fps_time_window (float): The time interval of a inference/drop fps calculation window.
        zip_tool(ZipBase): The zip tool.
    """

    def __init__(self, inference_engine: InferenceEngine,
                 infer_info: InferenceInfo,
                 infer_queue_connector: InferQueueClientBase,
                 infer_broker_connector: StreamBrokerClientBase,
                 pipeline_manager: PipelineManager,
                 fps_time_window: float,
                 zip_tool: ZipBase):
        """Initialize an InferenceTask object.

        Args:
            inference_engine (InferenceEngine): The inference engine instance.
            infer_info (InferenceInfo): The inference information.
            infer_queue_connector (InferQueueClientBase): The inference queue connector instance.
            infer_broker_connector (StreamBrokerClientBase): The inference stream broker connector
              instance.
            pipeline_manager (PipelineManager): The pipeline manager instance.
            infer_frame_count (dict): A dictonary that saves the inference frame counts for every
              pipeline.
            drop_frame_count (dict): A dictonary that saves the drop frame counts for every
              pipeline.
            infer_frame_count_sum (int): The sum of inference frame counts.
            drop_frame_count_sum (int): The sum of drop frame counts.
            infer_start_time (float): The start time of inference/drop frame counting.
            fps_time_window (float): The time interval of a inference/drop fps calculation window.
            zip_tool(ZipBase): The zip tool.
        """
        MicroServiceTask.__init__(self)
        self.inference_engine = inference_engine
        self.infer_info = infer_info
        self.infer_queue_connector = infer_queue_connector
        self.infer_broker_connector = infer_broker_connector
        self.pipeline_manager = pipeline_manager
        self.infer_frame_count = {}
        self.drop_frame_count = {}
        self.infer_frame_count_sum = 0
        self.drop_frame_count_sum = 0
        self.infer_start_time = 0.0
        self.fps_time_window = fps_time_window
        self.zip_tool = zip_tool

    def calculate_fps(self, frame: Frame, drop_count: int) -> None:
        """Calculate infer/drop FPS and export metrics.

        Args:
            frame (Frame): The frame being inferred when calculating FPS.
            drop_count (int): The count of dropped frames when calculating FPS.
        """
        now = time.time()
        if self.infer_start_time == 0.0:
            self.infer_start_time = now
            return

        elapsed_time = now - self.infer_start_time
        pipeline_id = frame.pipeline_id

        self.update_frame_counts(pipeline_id, drop_count)
        self.export_fps_metrics(pipeline_id, elapsed_time)

        if elapsed_time > self.fps_time_window:
            self.infer_start_time = now
            self.reset_frame_counts()

    def update_frame_counts(self, pipeline_id: str, drop_count: int) -> None:
        """Update the frame counts for inference and drop.

        Args:
            pipeline_id (str): The id of pipeline to update the frame counts.
            drop_count (int): The count of dropped frames when updating the frame counts.
        """
        if pipeline_id not in self.infer_frame_count:
            self.infer_frame_count[pipeline_id] = 0
        if pipeline_id not in self.drop_frame_count:
            self.drop_frame_count[pipeline_id] = 0

        self.infer_frame_count[pipeline_id] += 1
        self.drop_frame_count[pipeline_id] += drop_count
        self.infer_frame_count_sum += 1
        self.drop_frame_count_sum += drop_count

    def export_fps_metrics(self, pipeline_id: str, elapsed_time: float) -> None:
        """Export the calculated FPS metrics and save FPS of pipeline to Pipeline-table.

        Args:
            pipeline_id (str): The id of pipeline to save FPS to Pipeline-table.
            elapsed_time (float): The elapsed time to calculate FPS.
        """
        infer_fps_pipeline = round(self.infer_frame_count[pipeline_id] / elapsed_time)
        self.pipeline_manager.set_infer_fps(pipeline_id, self.infer_info, infer_fps_pipeline)

        infer_fps_sum = round(self.infer_frame_count_sum / elapsed_time)
        drop_fps_sum = round(self.drop_frame_count_sum / elapsed_time)

        metrics_manager.set_gauge('infer_fps', infer_fps_sum)
        metrics_manager.set_gauge('drop_fps', drop_fps_sum)
        LOG.info("infer_fps: %d", infer_fps_sum)
        LOG.info("drop_fps: %d", drop_fps_sum)

    def reset_frame_counts(self) -> None:
        """Reset the frame counts for the next calculation window."""
        for pipeline in list(self.infer_frame_count.keys()):
            self.infer_frame_count[pipeline] = 0
            self.drop_frame_count[pipeline] = 0
        self.infer_frame_count_sum = 0
        self.drop_frame_count_sum = 0

    def process_frame(self, frame: bytes) -> Frame:
        """Process the frame.

        Args:
            frame (bytes): frame get from the infer queue. 

        Returns:
            Frame: deserialized frame.

        Raises:
            TypeError: If the type of frame is not bytes.
            RuntimeError: If any errors while decoding or decompressing.
        """
        try:
            #decompress if zip is enable
            if self.zip_tool is not None:
                decompressed_data = self.zip_tool.decompress(src = frame)
            else:
                decompressed_data = frame
            #deserialize
            return Frame.from_blob(decompressed_data)
        except TypeError as e:
            raise TypeError(e) from e
        except RuntimeError as e:
            raise RuntimeError(e) from e

    def execute(self):
        """The task logic of inference task."""
        while not self.is_task_stopping:

            # 0. Create frame decryption actor
            decrypt_actor = QATFrameCipher()

            # 1. Get a frame from the infer queue and process the frame
            frame = self.infer_queue_connector.get_frame(
                self.infer_info.queue_topic)
            if frame is None:
                continue
            frame = self.process_frame(frame)
            drop_count = self.infer_queue_connector.drop(self.infer_info.queue_topic)
            topic = f"result-{frame.pipeline_id}"

            # 2. Decrypt frame
            frame.decrypt(decrypt_actor)

            # 3. decode frame raw data to image
            #image = cv2.imdecode(frame.raw, cv2.IMREAD_COLOR)

            # 4. Run inference on the frame
            prediction, predict_latency = self.inference_engine.predict(frame.raw)
            frame.raw = prediction
            LOG.info("Predict latency: %fms", predict_latency * 1000)

            time_after_predict = time.time()
            frame.timestamp_infer_end = time_after_predict
            streaming_to_inference_latency = time_after_predict - frame.timestamp_new_frame
            metrics_manager.observe_histogram('streaming_to_inference_latency',
                                              streaming_to_inference_latency)
            LOG.info("Latency between frame generation in streaming service and inference " +
                     "completion in inference service: %fms", streaming_to_inference_latency * 1000)

            # 5. encode the inference result
            #_, jpeg = cv2.imencode('.jpg', prediction)

            # 6. publish the inference result
            self.infer_broker_connector.publish_frame(topic, frame)

            # 7. Calculate infer/drop FPS and export metrics
            self.calculate_fps(frame, drop_count)

    def stop(self):
        """Stop the inference task."""
        MicroServiceTask.stop(self)
        if self.zip_tool is not None:
            del self.zip_tool

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
