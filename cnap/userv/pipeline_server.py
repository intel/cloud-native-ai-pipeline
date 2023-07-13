#!/usr/bin/python3
"""
Pipeline Server provides a Restful API to get pipeline data.
"""
import os
import sys
import logging
import signal
from multiprocessing import Process

from flask import Flask, jsonify, Response
from flask_cors import cross_origin

from core.rtdb import RedisDB, RuntimeDatabaseBase

LOG = logging.getLogger(__name__)

WEB_APP = Flask(__name__)
server = Process(target=WEB_APP.run, args=('0.0.0.0',))

def _get_env(key, default=None):
    if key not in os.environ:
        LOG.warning("Could not find the key %s in environment, "
                    "use default value %s", key, str(default))
        return default
    return os.environ[key]

class PipelineService:
    """
    Service to get pipeline data.
    """
    INFER_ENGINE_TABLE = "InferEngine-table"
    PIPELINE_TABLE = "Pipeline-table"

    _instance = None

    def __init__(self):
        self._db = None

    @property
    def db(self) -> RuntimeDatabaseBase:
        """
        Get the runtime database.

        Returns:
            RuntimeDatabaseBase: An instance of the RuntimeDatabaseBase class.

        Raises:
            NotImplementedError: If the runtime database type is not supported.
            redis.exceptions.ConnectionError: If connection to the Redis server fails.
        """
        if self._db is None:
            runtime_db_type = _get_env("RUNTIME_DB_TYPE", "redis")
            if runtime_db_type == "redis":
                self._db = RedisDB()
                redis_host = _get_env("REDIS_HOST", "127.0.0.1")
                redis_port = _get_env("REDIS_PORT", 6379)
                self._db.connect(redis_host, redis_port)
            else:
                # TODO: support other runtime database type
                LOG.error("Not supported runtime database type: %s", runtime_db_type)
                raise NotImplementedError(f"Runtime database type {runtime_db_type} \
                                          not supported yet.")
        return self._db

    @property
    def pipelines(self) -> list:
        """
        Gets the pipeline list.

        Returns:
            list: List of pipeline dictionaries.

        Raises:
            ValueError: If the pipeline table does not exist.
        """
        pipeline_dicts = self.db.get_all_table_objects_dict(PipelineService.PIPELINE_TABLE)
        inference_dicts = self.db.get_all_table_objects_dict(PipelineService.INFER_ENGINE_TABLE)

        pipelines = []

        for pipeline_id, pipeline_dict in pipeline_dicts.items():
            infer_id = pipeline_dict['info_engine_info']['id']
            pipeline = {
                'pipeline_id': pipeline_id,
                'model_name': inference_dicts[infer_id]['model']['details']['name'],
                'stream_name': pipeline_dict['provider']['name'],
                'input_fps': pipeline_dict['provider']['fps'],
                'infer_fps': 25
            }
            pipelines.append(pipeline)

        return pipelines

    @classmethod
    def inst(cls):
        """
        Singleton instance.

        Returns:
            PipelineService: An instance of the PipelineService class.
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

@WEB_APP.route('/api/pipelines', methods=['GET'])
@cross_origin(origin='*',headers=['Content-Type','Authorization'])
def api_get_pipelines() -> Response:
    """
    Restful API for getting pipeline data.

    Returns:
        Response: Flask response object with JSON data and status.
    """
    pipelines = PipelineService.inst().pipelines
    return jsonify(pipelines)

@WEB_APP.route('/healthz', methods=['GET'])
def health_check() -> Response:
    """
    Health check endpoint.

    Returns:
        Response: Flask response object with message and status.
    """
    return "Ok", 200

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(threadName)s %(message)s")

    inst = PipelineService.inst()
    server.start()

    def signal_handler(num, _):
        """
        Signal handler.

        Args:
            num (int): The received signal number.
        """
        LOG.error("signal %d", num)
        server.terminate()
        sys.exit(1)

    # setup the signal handler
    signames = ['SIGINT', 'SIGHUP', 'SIGQUIT', 'SIGUSR1', 'SIGTERM']
    for name in signames:
        signal.signal(getattr(signal, name), signal_handler)

    server.join()
