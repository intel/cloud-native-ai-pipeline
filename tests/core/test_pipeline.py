"""Tests for the pipeline module.

This module contains the tests for the pipeline module.

Functions:
    inference_info: Fixture for inference info.
    pipeline_instance: Fixture for pipeline.
    pipeline_manager: Fixture for pipeline manager.
    test_pipeline_id_setter: Tests the setter of _id attribute of Pipeline class.
    test_pipeline_iter: Tests the Iterator of Pipeline class.
    test_pipeline_manager_register_pipeline: Tests the register_pipeline method of the
      PipelineManager class.
    test_pipeline_manager_unregister_pipeline: Tests the unregister_pipeline method of the
      PipelineManager class.
    test_pipeline_manager_set_infer_fps: Tests the set_infer_fps method of the PipelineManager
      class.
    test_pipeline_manager_set_infer_fps_unregistered_pipeline: Tests the set_infer_fps method of
      the PipelineManager class with an unregistered pipeline.
"""

import uuid
import json

import pytest

from cnap.core import infereng, pipeline, stream

# pylint: disable=redefined-outer-name

TEST_STREAM_NAME = 'classroom'
TEST_DEVICE = 'cpu'
TEST_MODEL_ID = str(uuid.uuid1())
TEST_PIPELINE_ID = "2bbbdebe-3722-11ee-ba4a-d6bcdc58bce0"

@pytest.fixture
def filesource():
    """Fixture for file source stream provider.

    Returns:
        StreamProvider: A `StreamProvider` object instantiated as `FileSource`.
    """
    return stream.FileSource(TEST_STREAM_NAME)

@pytest.fixture
def inference_info():
    """Fixture for inference info.

    Returns:
        InferenceInfo: A `InferenceInfo` object.
    """
    return infereng.InferenceInfo(TEST_DEVICE, TEST_MODEL_ID)

@pytest.fixture
def pipeline_instance(filesource, inference_info):
    """Fixture for pipeline.

    Args:
        filesource (StreamProvider): Fixture for file source stream provider.
        inference_info (InferenceInfo): Fixture for inference info.

    Returns:
        Pipeline: A `Pipeline` object.
    """
    return pipeline.Pipeline(filesource, inference_info)

@pytest.fixture
def pipeline_manager(rtdb_connect):
    """Fixture for pipeline manager.

    Args:
        my_redis_client (Callable): Temporary redis client provided by pytest-redis's redisdb
          fixture.

    Returns:
        PipelineManager: A `PipelineManager` object.
    """
    pipeline_manager = pipeline.PipelineManager(rtdb_connect)
    return pipeline_manager

def test_pipeline_id_setter(pipeline_instance):
    """Tests the setter of _id attribute of Pipeline class.

    Args:
        pipeline_instance (Pipeline): Fixture for pipeline.
    """
    pipeline_instance.id = TEST_PIPELINE_ID
    assert pipeline_instance.id == TEST_PIPELINE_ID

def test_pipeline_iter(filesource, inference_info, pipeline_instance):
    """Tests the Iterator of Pipeline class.

    This test checks if the Iterator of Pipeline class can covert pipeline instance to
      dict successfully.

    Args:
        filesource (StreamProvider): Fixture for file source stream provider.
        inference_info (InferenceInfo): Fixture for inference info.
        pipeline_instance (Pipeline): Fixture for pipeline.
    """
    pipeline_dict = dict(pipeline_instance)
    assert pipeline_dict == {'provider': dict(filesource),
                             'info_engine_info': dict(inference_info),
                             'infer_fps': {}}

def test_pipeline_manager_register_pipeline(pipeline_instance, rtdb_connect, pipeline_manager):
    """Tests the register_pipeline method of the PipelineManager class.

    This test checks if the register_pipeline method can register a pipeline successfully.

    Args:
        pipeline_instance (Pipeline): Fixture for pipeline.
        rtdb_connect (RuntimeDatabaseBase): Fixture for Redis runtime database.
        pipeline_manager (PipelineManager): Fixture for pipeline manager.
    """
    pipeline_manager.register_pipeline(pipeline_instance)
    assert rtdb_connect.get_table_object_dict(pipeline_manager.PIPELINE_TABLE,
                    pipeline_instance.id) == json.loads(json.dumps(dict(pipeline_instance)))

def test_pipeline_manager_unregister_pipeline(pipeline_instance, rtdb_connect, pipeline_manager):
    """Tests the unregister_pipeline method of the PipelineManager class.

    This test checks if the unregister_pipeline method can unregister a pipeline successfully.

    Args:
        pipeline_instance (Pipeline): Fixture for pipeline.
        rtdb_connect (RuntimeDatabaseBase): Fixture for Redis runtime database.
        pipeline_manager (PipelineManager): Fixture for pipeline manager.
    """
    pipeline_manager.register_pipeline(pipeline_instance)
    pipeline_manager.unregister_pipeline(pipeline_instance.id)
    assert rtdb_connect.check_table_object_exist(pipeline_manager.PIPELINE_TABLE,
                                                         pipeline_instance.id) is False

def test_pipeline_manager_set_infer_fps(inference_info, pipeline_instance, rtdb_connect,
                                        pipeline_manager):
    """Tests the set_infer_fps method of the PipelineManager class.

    This test checks if the set_infer_fps method can set infer fps for a pipeline successfully.

    Args:
        inference_info (InferenceInfo): Fixture for inference info.
        pipeline_instance (Pipeline): Fixture for pipeline.
        rtdb_connect (RuntimeDatabaseBase): Fixture for Redis runtime database.
        pipeline_manager (PipelineManager): Fixture for pipeline manager.
    """
    pipeline_manager.register_pipeline(pipeline_instance)
    infer_fps = 15
    pipeline_manager.set_infer_fps(pipeline_instance.id, inference_info.id, infer_fps)
    assert rtdb_connect.get_table_object_dict(pipeline_manager.PIPELINE_TABLE,
                pipeline_instance.id)['infer_fps'][inference_info.id] == infer_fps

def test_pipeline_manager_set_infer_fps_unregistered_pipeline(inference_info, pipeline_instance,
                                                              pipeline_manager):
    """Tests the set_infer_fps method of the PipelineManager class with an unregistered pipeline.

    This test checks if the set_infer_fps method can be executed normally without raising any
    errors with an unregistered pipeline.

    Args:
        inference_info (InferenceInfo): Fixture for inference info.
        pipeline_instance (Pipeline): Fixture for pipeline.
        pipeline_manager (PipelineManager): Fixture for pipeline manager.
    """
    infer_fps = 15
    pipeline_manager.set_infer_fps(pipeline_instance.id, inference_info.id, infer_fps)
    assert True
