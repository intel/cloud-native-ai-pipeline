"""Tests for the inference engine module.

This module contains the tests for the inference engine module.

Functions:
    inference_info: Fixture for inference info.
    rtdb_connect: Fixture for Redis runtime database.
    inference_engine_manager: Fixture for inference engine manager.
    model_info: Fixture for model info.
    assert_inference_info_equal: Assert if two inference info are equal.
    test_inference_info_init_invalid_device: Tests the __init__ method of InferenceInfo class with
      invalid device.
    test_inference_info_id_setter: Tests the setter of _id attribute of InferenceInfo class.
    test_inference_info_queue_topic_setter: Tests the setter of _queue_topic attribute of
      InferenceInfo class.
    test_inference_info_queue_topic_property: Tests the property of _queue_topic attribute of
      InferenceInfo class.
    test_inference_info_input_size_property: Tests the property of _input_size attribute of
      InferenceInfo class.
    test_inference_info_iter: Tests the Iterator of InferenceInfo class.
    test_inference_engine_manager_search_engine: Tests the search_engine method of the
      InferEngineManager class.
    test_inference_engine_manager_search_engine_not_found: Tests the search_engine method when can't
      find a matching inference engine.
    test_inference_engine_manager_search_engine_invalid_key: Tests the search_engine method of the
      InferEngineManager class with invalid key.
    test_inference_engine_manager_register_engine: Tests the register_engine method of the
      InferEngineManager class.
    test_inference_engine_manager_unregister_engine: Tests the unregister_engine method of the
      InferEngineManager class.
"""

import uuid

import pytest
from pytest_redis import factories

from cnap.core import infereng, model, rtdb

# pylint: disable=redefined-outer-name

TEST_DEVICE = 'cpu'
TEST_MODEL_ID = str(uuid.uuid1())
TEST_INFERENCE_INFO_ID = str(uuid.uuid1())
TEST_FRAMEWORK = 'tensorflow'
TEST_TARGET = 'object-detection'
TEST_MODEL_NAME = 'ssdmobilenet'
TEST_MODEL_VERSION = '1.0'

REDIS_HOST = '0.0.0.0'
REDIS_PORT = 8080

my_redis_server = factories.redis_proc(host=REDIS_HOST, port=REDIS_PORT)
my_redis_client = factories.redisdb('my_redis_server')

@pytest.fixture
def inference_info():
    """Fixture for inference info.

    Returns:
        InferenceInfo: A `InferenceInfo` object.
    """
    return infereng.InferenceInfo(TEST_DEVICE, TEST_MODEL_ID)

@pytest.fixture
def rtdb_connect(my_redis_client):
    """Fixture for Redis runtime database.

    Args:
        my_redis_client (Callable): Temporary redis client provided by pytest-redis's redisdb
          fixture.

    Returns:
        RuntimeDatabaseBase: A `RuntimeDatabaseBase` object.
    """
    db = rtdb.RedisDB()
    db.connect(host=REDIS_HOST, port=REDIS_PORT)
    return db

@pytest.fixture
def inference_engine_manager(rtdb_connect):
    """Fixture for inference engine manager.

    Args:
        my_redis_client (Callable): Temporary redis client provided by pytest-redis's redisdb
          fixture.

    Returns:
        InferEngineManager: A `InferEngineManager` object.
    """
    inference_engine_manager = infereng.InferEngineManager(rtdb_connect)
    return inference_engine_manager

@pytest.fixture
def model_info():
    """Fixture for model info.

    Returns:
        ModelInfo: A `ModelInfo` object.
    """
    model_metrics = model.ModelMetrics(0,0,0,0,0)
    model_details = model.ModelDetails(TEST_MODEL_NAME, TEST_MODEL_VERSION, TEST_FRAMEWORK,
                                       TEST_TARGET, 'int8')
    model_info = model.ModelInfo(model_details, 0, model_metrics)
    model_info.id = TEST_MODEL_ID
    return model_info

def assert_inference_info_equal(inference_info1: infereng.InferenceInfo,
                                inference_info2: infereng.InferenceInfo):
    """Assert if two inference info are equal.

    Args:
        inference_info1 (InferenceInfo): The InferenceInfo to assert.
        inference_info2 (InferenceInfo): The InferenceInfo to assert.
    """
    assert inference_info1.id == inference_info2.id
    assert inference_info1.device == inference_info2.device
    assert inference_info1.model_id == inference_info2.model_id

def test_inference_info_init_invalid_device():
    """Tests the __init__ method of InferenceInfo class with invalid device."""
    with pytest.raises(ValueError):
        infereng.InferenceInfo('xxx', TEST_MODEL_ID)

def test_inference_info_id_setter(inference_info):
    """Tests the setter of _id attribute of InferenceInfo class.

    Args:
        inference_info (InferenceInfo): Fixture for InferenceInfo.
    """
    inference_info.id = TEST_INFERENCE_INFO_ID
    assert inference_info.id == TEST_INFERENCE_INFO_ID

def test_inference_info_queue_topic_setter(inference_info):
    """Tests the setter of _queue_topic attribute of InferenceInfo class.

    Args:
        inference_info (InferenceInfo): Fixture for InferenceInfo.
    """
    test_queue_topic = f"origin-{TEST_MODEL_ID}-{TEST_DEVICE}"
    inference_info.queue_topic = test_queue_topic
    assert inference_info.queue_topic == test_queue_topic

def test_inference_info_queue_topic_property(inference_info):
    """Tests the property of _queue_topic attribute of InferenceInfo class.

    Args:
        inference_info (InferenceInfo): Fixture for InferenceInfo.
    """
    assert inference_info.queue_topic == f"origin-{TEST_MODEL_ID}-{TEST_DEVICE}"

def test_inference_info_input_size_property(inference_info):
    """Tests the property of _input_size attribute of InferenceInfo class.

    Args:
        inference_info (InferenceInfo): Fixture for InferenceInfo.
    """
    assert inference_info.input_size == (infereng.DEFAULT_INPUT_WIDTH,
                                         infereng.DEFAULT_INPUT_HEIGHT)

def test_inference_info_iter(inference_info, model_info):
    """Tests the Iterator of InferenceInfo class.

    This test checks if the Iterator of InferenceInfo class can covert InferenceInfo instance to
    dict successfully.

    Args:
        inference_info (InferenceInfo): Fixture for InferenceInfo.
        model_info (ModelInfo): Fixture for ModelInfo.
    """
    inference_info.id = TEST_INFERENCE_INFO_ID
    inference_info_dict = dict(inference_info)
    assert inference_info_dict == {'id': TEST_INFERENCE_INFO_ID,
                                   'device': TEST_DEVICE,
                                   'model_id': TEST_MODEL_ID}

def test_inference_engine_manager_search_engine(inference_engine_manager, inference_info,
                                                model_info):
    """Tests the search_engine method of the InferEngineManager class.

    This test checks if the search_engine method can search inference engine successfully.

    Args:
        inference_engine_manager (InferEngineManager): Fixture for InferEngineManager.
        inference_info (InferenceInfo): Fixture for Redis InferenceInfo.
        model_info (ModelInfo): Fixture for ModelInfo.
    """
    inference_engine_manager.register_engine(inference_info, model_info)
    searched_inference_info = inference_engine_manager.search_engine(TEST_FRAMEWORK, TEST_TARGET,
            TEST_DEVICE, TEST_MODEL_NAME, TEST_MODEL_VERSION)
    assert_inference_info_equal(searched_inference_info, inference_info)

def test_inference_engine_manager_search_engine_not_found(inference_engine_manager, inference_info,
                                                       model_info):
    """Tests the search_engine method when can't find a matching inference engine.

    Args:
        inference_engine_manager (InferEngineManager): Fixture for InferEngineManager.
        inference_info (InferenceInfo): Fixture for Redis InferenceInfo.
        model_info (ModelInfo): Fixture for ModelInfo.
    """
    inference_engine_manager.register_engine(inference_info, model_info)
    searched_inference_info = inference_engine_manager.search_engine(TEST_FRAMEWORK, TEST_TARGET,
            'xxx', TEST_MODEL_NAME, TEST_MODEL_VERSION)
    assert searched_inference_info is None

def test_inference_engine_manager_search_engine_invalid_key(inference_engine_manager,
                                                            inference_info, rtdb_connect):
    """Tests the search_engine method of the InferEngineManager class with invalid key.

    Args:
        inference_engine_manager (InferEngineManager): Fixture for InferEngineManager.
        inference_info (InferenceInfo): Fixture for Redis InferenceInfo.
        model_info (ModelInfo): Fixture for ModelInfo.
    """
    rtdb_connect.save_table_object_dict(infereng.INFER_ENGINE_TABLE, inference_info.id,
                                        dict(inference_info))
    searched_inference_info = inference_engine_manager.search_engine(TEST_FRAMEWORK, TEST_TARGET,
            TEST_DEVICE, TEST_MODEL_NAME, TEST_MODEL_VERSION)
    assert searched_inference_info is None

def test_inference_engine_manager_register_engine(inference_engine_manager, inference_info,
                                                  model_info, rtdb_connect):
    """Tests the register_engine method of the InferEngineManager class.

    This test checks if the register_engine method can register an inference engine successfully.

    Args:
        inference_engine_manager (InferEngineManager): Fixture for InferEngineManager.
        inference_info (InferenceInfo): Fixture for Redis InferenceInfo.
        model_info (ModelInfo): Fixture for ModelInfo.
        rtdb_connect (RuntimeDatabaseBase): Fixture for Redis runtime database.
    """
    inference_engine_manager.register_engine(inference_info, model_info)
    expected_data = {
        'infer': dict(inference_info),
        'model': dict(model_info)
    }
    assert rtdb_connect.get_table_object_dict(infereng.INFER_ENGINE_TABLE,
                    inference_info.id) == expected_data

def test_inference_engine_manager_unregister_engine(inference_engine_manager, inference_info,
                                                    model_info, rtdb_connect):
    """Tests the unregister_engine method of the InferEngineManager class.

    This test checks if the unregister_engine method can unregister an inference engine
    successfully.

    Args:
        inference_engine_manager (InferEngineManager): Fixture for InferEngineManager.
        inference_info (InferenceInfo): Fixture for Redis InferenceInfo.
        model_info (ModelInfo): Fixture for ModelInfo.
        rtdb_connect (RuntimeDatabaseBase): Fixture for Redis runtime database.
    """
    inference_engine_manager.register_engine(inference_info, model_info)
    inference_engine_manager.unregister_engine(inference_info.id)
    assert rtdb_connect.check_table_object_exist(infereng.INFER_ENGINE_TABLE,
                                                         inference_info.id) is False
