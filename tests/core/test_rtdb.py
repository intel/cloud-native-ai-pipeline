"""Tests for the runtime database.

This module contains the tests for the runtime database module.

Functions:
    data_config: Fixture for test data configurations.
    test_redis_runtime_database_connect: Tests the connect method of the RedisDB class.
    test_redis_runtime_database_connect_failed: Tests the connect method of the RedisDB class when
      the connection fails.
    test_redis_runtime_database_save_table_object_dict: Tests the save_table_object_dict method of
      the RedisDB class.
    test_redis_runtime_database_save_table_object_dict_failed: Tests the save_table_object_dict
      method with the value can't be serialized into JSON.
    test_redis_runtime_database_get_table_object_dict: Tests the get_table_object_dic method of the
      RedisDB class.
    test_redis_runtime_database_get_table_object_dict_not_found: Tests the get_table_object_dict
      method of the RedisDB class when object not found.
    test_redis_runtime_database_get_table_object_dict_json_decode_error: Tests the
      get_table_object_dict method of the RedisDB class with json decode error of object.
    test_redis_runtime_database_get_all_table_object_dict: Tests the get_all_table_object_dict
      method of the RedisDB class.
    test_redis_runtime_database_get_all_table_object_dict_not_found: Tests the
      get_all_table_object_dict method of the RedisDB class when object not found.
    test_redis_runtime_database_get_all_table_object_dict_json_decode_error: Tests the
      get_all_table_object_dict method of the RedisDB class with json decode error.
    test_redis_runtime_database_check_table_object_exist: Tests the check_table_object_exist method
      of the RedisDB class.
    test_redis_runtime_database_del_table_object: Tests the del_table_object method of the RedisDB
      class.
    test_invalid_table_param: Tests the methods of the RedisDB class with invalid table param.
    test_invalid_obj_param: Tests the methods of the RedisDB class with invalid obj param.
"""

import json

import pytest
import redis.exceptions

from cnap.core import rtdb
from tests.core.conftest import REDIS_HOST

# pylint: disable=redefined-outer-name

@pytest.fixture
def data_config():
    """Fixture for test data configurations.

    Returns:
        dict: A dict for test configurations.
    """
    config = {'table': 'test-table',
              'obj': 'test-obj',
              'dict': 'test-value'}
    return config

def test_redis_runtime_database_connect(rtdb_connect):
    """Tests the connect method of the RedisDB class.

    This test checks if the connect method can connect to redis server successfully.

    Args:
        my_redis_client (Callable): Temporary redis client provided by pytest-redis's redisdb
          fixture.
        rtdb_connect (RuntimeDatabaseBase): Fixture for Redis runtime database.
    """
    assert rtdb_connect._conn.ping() # pylint: disable=protected-access

def test_redis_runtime_database_connect_failed(my_redis_client):
    """Tests the connect method of the RedisDB class when the connection fails.

    Args:
        my_redis_client (Callable): Temporary redis client provided by pytest-redis's redisdb
          fixture.
    """
    REDIS_PORT_WRONG = 8001
    db = rtdb.RedisDB()
    with pytest.raises(redis.exceptions.ConnectionError):
        db.connect(host=REDIS_HOST, port=REDIS_PORT_WRONG)

def test_redis_runtime_database_save_table_object_dict(my_redis_client, rtdb_connect, data_config):
    """Tests the save_table_object_dict method of the RedisDB class.

    This test checks if the save_table_object_dict method can save a dict value for an object in a
    table on redis server successfully.

    Args:
        my_redis_client (Callable): Temporary redis client provided by pytest-redis's redisdb
          fixture.
        rtdb_connect (RuntimeDatabaseBase): Fixture for Redis runtime database.
        data_config (dict): Fixture for test data configurations.
    """
    rtdb_connect.save_table_object_dict(data_config['table'], data_config['obj'],
                                        data_config['dict'])
    assert my_redis_client.hget(data_config['table'], data_config['obj']) \
            == json.dumps(data_config['dict']).encode()

def test_redis_runtime_database_save_table_object_dict_failed(my_redis_client, rtdb_connect,
                                                              data_config):
    """Tests the save_table_object_dict method with the value can't be serialized into JSON.

    Args:
        my_redis_client (Callable): Temporary redis client provided by pytest-redis's redisdb
          fixture.
        rtdb_connect (RuntimeDatabaseBase): Fixture for Redis runtime database.
        data_config (dict): Fixture for test data configurations.
    """

    with pytest.raises(TypeError):
        rtdb_connect.save_table_object_dict(data_config['table'], data_config['obj'], rtdb_connect)

def test_redis_runtime_database_get_table_object_dict(my_redis_client, rtdb_connect, data_config):
    """Tests the get_table_object_dict method of the RedisDB class.

    This test checks if the get_table_object_dic method can get a dict value for an object from a
    table on redis server successfully.

    Args:
        my_redis_client (Callable): Temporary redis client provided by pytest-redis's redisdb
          fixture.
        rtdb_connect (RuntimeDatabaseBase): Fixture for Redis runtime database.
        data_config (dict): Fixture for test data configurations.
    """
    my_redis_client.hset(data_config['table'], data_config['obj'], json.dumps(data_config['dict']))
    assert rtdb_connect.get_table_object_dict(data_config['table'], data_config['obj']) \
            == data_config['dict']

def test_redis_runtime_database_get_table_object_dict_not_found(my_redis_client, rtdb_connect,
                                                             data_config):
    """Tests the get_table_object_dict method of the RedisDB class when object not found.

    This test checks if the get_table_object_dic method can get a dict value for an object from a
    table on redis server successfully.

    Args:
        my_redis_client (Callable): Temporary redis client provided by pytest-redis's redisdb
          fixture.
        rtdb_connect (RuntimeDatabaseBase): Fixture for Redis runtime database.
        data_config (dict): Fixture for test data configurations.
    """
    assert rtdb_connect.get_table_object_dict(data_config['table'], data_config['obj']) == {}

def test_redis_runtime_database_get_table_object_dict_json_decode_error(my_redis_client,
                                                                        rtdb_connect, data_config):
    """Tests the get_table_object_dict method of the RedisDB class with json decode error of object.

    This test checks if the get_table_object_dic method can get a dict value for an object from a
    table on redis server successfully.

    Args:
        my_redis_client (Callable): Temporary redis client provided by pytest-redis's redisdb
          fixture.
        rtdb_connect (RuntimeDatabaseBase): Fixture for Redis runtime database.
        data_config (dict): Fixture for test data configurations.
    """
    my_redis_client.hset(data_config['table'], data_config['obj'], data_config['dict'])
    assert rtdb_connect.get_table_object_dict(data_config['table'], data_config['obj']) == {}

def test_redis_runtime_database_get_all_table_object_dict(my_redis_client, rtdb_connect):
    """Tests the get_all_table_object_dict method of the RedisDB class.

    This test checks if the get_all_table_object_dict method can get all dict values from a table
    on redis server successfully.

    Args:
        my_redis_client (Callable): Temporary redis client provided by pytest-redis's redisdb
          fixture.
        rtdb_connect (RuntimeDatabaseBase): Fixture for Redis runtime database.
    """
    table = 'test-table'
    obj0 = 'test-obj0'
    d0 = {'test-key0': 'test-value0'}
    obj1 = 'test-obj1'
    d1 = {'test-key1': 'test-value1'}

    my_redis_client.hset(table, obj0, json.dumps(d0))
    my_redis_client.hset(table, obj1, json.dumps(d1))
    assert rtdb_connect.get_all_table_objects_dict(table) == {obj0: d0, obj1: d1}

def test_redis_runtime_database_get_all_table_object_dict_not_found(my_redis_client, rtdb_connect,
                                                                 data_config):
    """Tests the get_all_table_object_dict method of the RedisDB class when object not found.

    This test checks if the get_all_table_object_dict method can get all dict values from a table
    on redis server successfully.

    Args:
        my_redis_client (Callable): Temporary redis client provided by pytest-redis's redisdb
          fixture.
        rtdb_connect (RuntimeDatabaseBase): Fixture for Redis runtime database.
        data_config (dict): Fixture for test data configurations.
    """
    assert rtdb_connect.get_all_table_objects_dict(data_config['table']) == {}

def test_redis_runtime_database_get_all_table_object_dict_json_decode_error(
        my_redis_client, rtdb_connect, data_config):
    """Tests the get_all_table_object_dict method of the RedisDB class with json decode error.

    This test checks if the get_all_table_object_dict method can get all dict values from a table
    on redis server successfully.

    Args:
        my_redis_client (Callable): Temporary redis client provided by pytest-redis's redisdb
          fixture.
        rtdb_connect (RuntimeDatabaseBase): Fixture for Redis runtime database.
        data_config (dict): Fixture for test data configurations.
    """
    my_redis_client.hset(data_config['table'], data_config['obj'], data_config['dict'])
    assert rtdb_connect.get_all_table_objects_dict(data_config['table']) == {}

def test_redis_runtime_database_check_table_object_exist(my_redis_client, rtdb_connect,
                                                         data_config):
    """Tests the check_table_object_exist method of the RedisDB class.

    This test checks if the check_table_object_exist method can check whether a given object exists
    in a given table on redis server successfully.

    Args:
        my_redis_client (Callable): Temporary redis client provided by pytest-redis's redisdb
          fixture.
        rtdb_connect (RuntimeDatabaseBase): Fixture for Redis runtime database.
        data_config (dict): Fixture for test data configurations.
    """
    my_redis_client.hset(data_config['table'], data_config['obj'], json.dumps(data_config['dict']))
    assert rtdb_connect.check_table_object_exist(data_config['table'], data_config['obj']) is True

def test_redis_runtime_database_del_table_object(my_redis_client, rtdb_connect, data_config):
    """Tests the del_table_object method of the RedisDB class.

    This test checks if the del_table_object method can delete an object from a given table
    on redis server successfully.

    Args:
        my_redis_client (Callable): Temporary redis client provided by pytest-redis's redisdb
          fixture.
        rtdb_connect (RuntimeDatabaseBase): Fixture for Redis runtime database.
        data_config (dict): Fixture for test data configurations.
    """
    my_redis_client.hset(data_config['table'], data_config['obj'], json.dumps(data_config['dict']))
    rtdb_connect.del_table_object(data_config['table'], data_config['obj'])
    assert my_redis_client.hexists(data_config['table'], data_config['obj']) is False

def test_invalid_table_param(my_redis_client, rtdb_connect, data_config):
    """Tests the methods of the RedisDB class with invalid table param.

    Args:
        my_redis_client (Callable): Temporary redis client provided by pytest-redis's redisdb
          fixture.
        rtdb_connect (RuntimeDatabaseBase): Fixture for Redis runtime database.
        data_config (dict): Fixture for test data configurations.
    """
    data_config['table'] = None

    with pytest.raises(ValueError):
        rtdb_connect.save_table_object_dict(data_config['table'], data_config['obj'],
                                            data_config['dict'])
    with pytest.raises(ValueError):
        rtdb_connect.get_table_object_dict(data_config['table'], data_config['obj'])
    with pytest.raises(ValueError):
        rtdb_connect.get_all_table_objects_dict(data_config['table'])
    with pytest.raises(ValueError):
        rtdb_connect.check_table_object_exist(data_config['table'], data_config['obj'])
    with pytest.raises(ValueError):
        rtdb_connect.del_table_object(data_config['table'], data_config['obj'])

def test_invalid_obj_param(my_redis_client, rtdb_connect, data_config):
    """Tests the methods of the RedisDB class with invalid obj param.

    Args:
        my_redis_client (Callable): Temporary redis client provided by pytest-redis's redisdb
          fixture.
        rtdb_connect (RuntimeDatabaseBase): Fixture for Redis runtime database.
        data_config (dict): Fixture for test data configurations.
    """
    data_config['obj'] = None

    with pytest.raises(ValueError):
        rtdb_connect.save_table_object_dict(data_config['table'], data_config['obj'],
                                            data_config['dict'])
    with pytest.raises(ValueError):
        rtdb_connect.get_table_object_dict(data_config['table'], data_config['obj'])
    with pytest.raises(ValueError):
        rtdb_connect.check_table_object_exist(data_config['table'], data_config['obj'])
    with pytest.raises(ValueError):
        rtdb_connect.del_table_object(data_config['table'], data_config['obj'])
