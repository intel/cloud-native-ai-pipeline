"""A Streaming Service module.

This module contains the implementation of the StreamingService and StreamingTask classes,
which are used to run streaming service.

Classes:
    StreamingService: A concrete class implementing the MicroAppBase for streaming Service.
    StreamingTask: A concrete class of MicroServiceTask for streaming task.
"""
import logging
import time
import sys
import signal
import os
from typing import Optional

from core.rtdb import RedisDB, RuntimeDatabaseBase
from core.pipeline import Pipeline, PipelineManager
from core.infereng import InferEngineManager, InferenceInfo
from core.stream import StreamProvider, create_stream_from_type, FileSource
from core.filedb import LocalFileDatabase
from core.frame import Frame, QATFrameCipher
from core.inferqueue import RedisInferQueueClient, KafkaInferQueueClient, InferQueueClientBase
from userv.uapp import MicroAppBase, MicroServiceTask

LOG = logging.getLogger(__name__)
CURR_DIR = os.path.dirname(os.path.abspath(__file__))

# pylint: disable=too-many-instance-attributes

class StreamingService(MicroAppBase):
    """A concrete class implementing the MicroAppBase for Streaming Service.

    Streaming service, read frames from the stream provider, and process frames,
    then publish frames to inference queue.

    Attributes:
        _db (RuntimeDatabaseBase): The runtime database instance.
        _provider (StreamProvider): The stream provider instance.
        _infer_engine_manager (InferEngineManager): The inference engine manager instance.
        _pipeline_manager (PipelineManager): The pipeline manager instance.
        _infer_engine_info (Optional[InferenceInfo]): The infer engine info instance.
        _pipeline (Pipeline): The pipeline instance.
        _is_stopping (bool): A boolean variable that flags if the service is stopping or not.
        _infer_queue_connector (InferQueueClientBase): The inference queue connector instance.
    """
    def __init__(self):
        """Initialize a StreamingService object."""
        MicroAppBase.__init__(self)
        self._db = None
        self._provider = None
        self._infer_engine_manager = None
        self._pipeline_manager = None
        self._infer_engine_info = None
        self._pipeline = None
        self._is_stopping = False
        self._infer_queue_connector = None

    @property
    def db(self) -> RuntimeDatabaseBase:
        """The runtime database instance.

        If `_db` is None, this function will create a `RuntimeDatabaseBase` object
        and connect to runtime database.

        Returns:
            RuntimeDatabaseBase: An instance of the RuntimeDatabaseBase class.

        Raises:
            NotImplementedError: If the runtime database type is not supported yet.
            redis.exceptions.ConnectionError: If connection to the Redis server fails
                and reconnection exceeds the limit.
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
                                          is not supported yet. ")
        return self._db

    @property
    def provider(self) -> StreamProvider:
        """The stream provider instance.

        If `_provider` is None, this function will create a `StreamProvider` object.

        Returns:
            StreamProvider: An instance of StreamProvider class.

        Raises:
            NotImplementedError: If the file database type is not supported.
            ValueError: If the provider type is invalid.
        """
        if self._provider is None:
            provider_type = self.get_env("PROVIDER_TYPE", "file")
            provider_name = self.get_env("PROVIDER_NAME", "classroom")
            provider_pathname = self.get_env("PROVIDER_PATHNAME", "classroom.mp4")

            self._provider = create_stream_from_type(
                provider_type,
                provider_name,
                provider_pathname)
            if provider_type == "file":
                file_db_type = self.get_env("FILE_DB_TYPE", "local")
                if file_db_type == "local":
                    self._provider.file_db = LocalFileDatabase(os.path.join(
                            CURR_DIR, "../../sample-videos"))
                else:
                    # TODO: support other file database
                    LOG.error("Not supported file database type: %s", file_db_type)
                    raise NotImplementedError(f"File database type {file_db_type} \
                                              is not supported yet.")
        return self._provider

    @property
    def infer_engine_manager(self) -> InferEngineManager:
        """The inference engine manager instance.

        If `_infer_engine_manager` is None, this function will create a `InferEngineManager` object.

        Returns:
            InferEngineManager: An instance of InferEngineManager class.
        """
        if self._infer_engine_manager is None:
            self._infer_engine_manager = InferEngineManager(self.db)
        return self._infer_engine_manager

    @property
    def infer_queue_connector(self) -> InferQueueClientBase:
        """The inference queue connector instance.

        If `_infer_queue_connector` is None, this function will create a `InferQueueClientBase`
        object and connect to queue server.

        Returns:
            InferQueueClientBase: An instance of InferQueueClientBase class.

        Raises:
            NotImplementedError: If the queue type is not supported.
            redis.exceptions.ConnectionError: If connection to the Redis server fails
                and reconnection exceeds the limit.
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
                raise NotImplementedError(f"Inference queue type {queue_type} \
                                              is not supported yet.")
            self._infer_queue_connector.connect(queue_host, queue_port)
        return self._infer_queue_connector

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
    def pipeline(self) -> Pipeline:
        """The pipeline instance."""
        return self._pipeline

    @property
    def infer_engine_info(self) -> Optional[InferenceInfo]:
        """The infer engine info instance.

        If `infer_engine_info` is None, this function will search the matching inference engine.

        Returns:
            InferenceInfo: An instance of InferenceInfo class.
            None: The requested inference engine was not found.
        """
        if self._infer_engine_info is None:
            req_framework = self.get_env("INFER_FRAMEWORK", "tensorflow")
            req_target = self.get_env("INFER_TARGET", "object-detection")
            req_device = self.get_env("INFER_DEVICE", "cpu")
            req_model_name = self.get_env("INFER_MODEL_NAME", "ssdmobilenet")
            req_model_version = self.get_env("INFER_MODEL_VERSION", "1.0")

            self._infer_engine_info = \
                self.infer_engine_manager.search_engine(
                    req_framework, req_target, req_device,
                    req_model_name, req_model_version)
            if self._infer_engine_info is None:
                LOG.error("Fail to match the inference engine")
                return None
        return self._infer_engine_info

    def init(self):
        """Initialization."""

    def cleanup(self):
        """Cleanup.

        Sets the stopping flag and performs necessary cleanup actions.
        """
        self._is_stopping = True
        LOG.debug("cleanup")
        if self.provider is not None:
            self.provider.close()

        if self.pipeline is not None and self.pipeline_manager is not None:
            self.pipeline_manager.unregister_pipeline(self.pipeline.id)

    def run(self) -> bool:
        """The main logic of streaming service.

        Returns:
            A bool object that flags whether the streaming service run sunccessfully.
        """
        if self.db is None or self.provider is None:
            return False

        if not self.provider.verify():
            LOG.error("Fail to verify the provider")
            return False

        while self.infer_engine_info is None:
            time.sleep(1)

        self._pipeline = Pipeline(self.provider, self.infer_engine_info)
        self.pipeline_manager.register_pipeline(self._pipeline)

        task = StreamingTask(self.provider, self.infer_engine_info,
                             self.infer_queue_connector, self._pipeline.id)
        task.start()

        return True

class StreamingTask(MicroServiceTask):
    """A concrete class of MicroServiceTask for streaming task.

    Attributes:
        provider(StreamProvider): The stream provider of streaming task.
        infer_engine_info(InferenceInfo): The inference information of streaming task.
        infer_queue_connector(InferQueueClientBase): The inference queue client of streaming task.
        pipeline_id(str): The pipeline id of streaming task.
    """
    def __init__(self, provider: StreamProvider,
                 infer_engine_info: InferenceInfo,
                 infer_queue_connector: InferQueueClientBase,
                 pipeline_id: str):
        """Initialize a StreamingTask object.

        Args:
            provider(StreamProvider): The stream provider of streaming task.
            infer_engine_info(InferenceInfo): The inference information of streaming task.
            infer_queue_connector(InferQueueClientBase): The inference queue client of streaming
              task.
            pipeline_id(str): The pipeline id of streaming task.
        """
        MicroServiceTask.__init__(self)
        self.provider = provider
        self.pipeline_id = pipeline_id
        self.infer_engine_info = infer_engine_info
        self.infer_queue_connector = infer_queue_connector

    def execute(self):
        """The task logic of streaming task."""
        self.provider.open()
        while not self.is_task_stopping:

            # 0. Create frame encryptor
            encrypt_actor = QATFrameCipher()

            # 1. Get a frame from provider
            raw_frame = self.provider.read_raw_frame()
            if raw_frame is None:
                break
            frame = Frame(self.provider, self.pipeline_id, Frame.get_sequence(), raw_frame)

            # 2. Normalize the frame according to model information
            frame.normalize(self.infer_engine_info.input_size)

            # 3. Encrypt frame before publishing to queue service out of TEE
            frame.encrypt(encrypt_actor)

            # 4. Stop the service if the inference queue for the topic is not available.
            if not self.infer_queue_connector.infer_queue_available(
                self.infer_engine_info.queue_topic):
                LOG.error("The inference queue for the topic is not available, \
                          stop publishing frames.")
                break

            # 5. publish the infer queue
            self.infer_queue_connector.publish_frame(
                self.infer_engine_info.queue_topic, frame)

            # 6. Prepare next loop
            if isinstance(self.provider, FileSource):
                if self.provider.target_fps != -1:
                    time.sleep(float(1/self.provider.target_fps))
                else:
                    time.sleep(float(1/self.provider.raw_fps))
            LOG.debug("Frame[%d] ts=%d", frame.sequence,
                      frame.timestamp_new_frame)
        self.provider.close()
        self.provider = None

    def stop(self):
        """Stop the streaming task."""
        MicroServiceTask.stop(self)
        if self.provider is not None:
            self.provider.close()

def entry() -> None:
    """The entry of Streaming Service."""
    app = StreamingService()

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
