"""Tests for the inference queue module.

This module contains the tests for the inference queue module.

Functions:
    redis_queue_client: Fixture for Redis inferqueue client.
    kafka_queue_client: Fixture for Kafka inferqueue client.
    test_redis_infer_queue_client_connect: Tests the connect method of the RedisInferQueueClient
      class.
    test_redis_infer_queue_client_connect_failed: Tests the connect method of the
      RedisInferQueueClient class when the connection fails.
    test_redis_infer_queue_client_publish_frame: Tests the publish_frame method of the
      RedisInferQueueClient class.
    test_redis_infer_queue_client_get_frame: Tests the get_frame method of the RedisInferQueueClient
      class.
    test_redis_infer_queue_client_drop: Tests the drop method of the RedisInferQueueClient class.
    test_redis_infer_queue_client_register_infer_queue: Tests the register_infer_queue method of the
      RedisInferQueueClient class.
    test_redis_infer_queue_client_unregister_infer_queue: Tests the unregister_infer_queue method of
      the RedisInferQueueClient class.
    test_redis_infer_queue_client_infer_queue_available: Tests the infer_queue_available method of
      the RedisInferQueueClient class.
    test_kafka_infer_queue_client_connect: Tests the connect method of the KafkaInferQueueClient
      class.
    test_kafka_infer_queue_client_connect_failed: Tests the connect method of the
      KafkaInferQueueClient class when the connection fails.
    test_kafka_infer_queue_client_publish_frame: Tests the publish_frame method of the
      KafkaInferQueueClient class.
    test_invalid_topic: Tests the methods of infer queue client classes with invalid topic param.
    test_publish_frame_invalid_frame: Tests the publish_frame method with invalid frame.
    test_get_frame_empty_queue: Tests the get_frame method when the infer queue is empty.
"""

import pytest
import redis.exceptions
from kafka import KafkaConsumer
import kafka.errors

from cnap.core import inferqueue
from tests.core.conftest import KAFKA_HOST, KAFKA_PORT, REDIS_HOST, REDIS_PORT

TEST_TOPIC = "origin-bd182f3a-5030-411f-819f-0ecc29360c76-cpu"

# pylint: disable=redefined-outer-name

@pytest.fixture(scope="module")
def redis_queue_client(my_redis_server):
    """Fixture for Redis inferqueue client.

    Args:
        my_redis_server (Callable): Temporary redis server provided by pytest-redis's redisdb
          fixture.

    Returns:
        RedisInferQueueClient: A `RedisInferQueueClient` object.
    """
    queue_conn = inferqueue.RedisInferQueueClient()
    queue_conn.connect(host=REDIS_HOST, port=REDIS_PORT)
    return queue_conn

@pytest.fixture(scope="module")
def kafka_queue_client(kafka_broker):
    """Fixture for Kafka inferqueue client.

    Args:
        kafka_broker (Container): Fixture for kafka broker server.

    Returns:
        KafkaInferQueueClient: A `KafkaInferQueueClient` object.
    """
    queue_client = inferqueue.KafkaInferQueueClient()
    queue_client.connect(host=KAFKA_HOST, port=KAFKA_PORT)
    return queue_client

def test_redis_infer_queue_client_connect(redis_queue_client):
    """Tests the connect method of the RedisInferQueueClient class.

    This test checks if the connect method can connect to redis server successfully.

    Args:
        redis_queue_client (RedisInferQueueClient): Fixture for RedisInferQueueClient.
    """
    assert redis_queue_client._conn.ping() # pylint: disable=protected-access

def test_redis_infer_queue_client_connect_failed(my_redis_server):
    """Tests the connect method of the RedisInferQueueClient class when the connection fails.

    Args:
        my_redis_server (Callable): Temporary redis server provided by pytest-redis's redisdb
          fixture.
    """
    REDIS_PORT_WRONG = 8001
    queue_client = inferqueue.RedisInferQueueClient()
    with pytest.raises(redis.exceptions.ConnectionError):
        queue_client.connect(host=REDIS_HOST, port=REDIS_PORT_WRONG)

def test_redis_infer_queue_client_publish_frame(redis_queue_client, frame_instance,
                                                my_redis_client):
    """Tests the publish_frame method of the RedisInferQueueClient class.

    This test checks if the publish_frame method can publish frame to redis server successfully.

    Args:
        redis_queue_client (RedisInferQueueClient): Fixture for RedisInferQueueClient.
        frame_instance (Frame): Fixture for Frame.
        my_redis_client (Callable): Temporary redis client provided by pytest-redis's redisdb
          fixture.
    """
    frame_blob = frame_instance.to_blob()
    redis_queue_client.publish_frame(TEST_TOPIC, frame_blob)
    assert my_redis_client.lpop(TEST_TOPIC) == frame_blob

def test_redis_infer_queue_client_get_frame(redis_queue_client, frame_instance, my_redis_client):
    """Tests the get_frame method of the RedisInferQueueClient class.

    This test checks if the get_frame method can get frame from redis server successfully.

    Args:
        redis_queue_client (RedisInferQueueClient): Fixture for RedisInferQueueClient.
        frame_instance (Frame): Fixture for Frame.
        my_redis_client (Callable): Temporary redis client provided by pytest-redis's redisdb
          fixture.
    """
    frame_blob = frame_instance.to_blob()
    my_redis_client.rpush(TEST_TOPIC, frame_blob)
    assert redis_queue_client.get_frame(TEST_TOPIC) == frame_blob

def test_redis_infer_queue_client_drop(redis_queue_client, frame_instance, my_redis_client):
    """Tests the drop method of the RedisInferQueueClient class.

    This test checks if the drop method can drop frames overflow the buffer successfully.

    Args:
        redis_queue_client (RedisInferQueueClient): Fixture for RedisInferQueueClient.
        frame_instance (Frame): Fixture for Frame.
        my_redis_client (Callable): Temporary redis client provided by pytest-redis's redisdb
          fixture.
    """
    frame_blob = frame_instance.to_blob()
    for _ in range(redis_queue_client.buffer_len + 2):
        redis_queue_client.publish_frame(TEST_TOPIC, frame_blob)
    assert redis_queue_client.drop(TEST_TOPIC) == 2
    assert my_redis_client.llen(TEST_TOPIC) == redis_queue_client.buffer_len

def test_redis_infer_queue_client_register_infer_queue(redis_queue_client, my_redis_client):
    """Tests the register_infer_queue method of the RedisInferQueueClient class.

    This test checks if the register_infer_queue method can register the topic in Redis inference
    queue successfully.

    Args:
        redis_queue_client (RedisInferQueueClient): Fixture for RedisInferQueueClient.
        my_redis_client (Callable): Temporary redis client provided by pytest-redis's redisdb
          fixture.
    """
    redis_queue_client.register_infer_queue(TEST_TOPIC)
    assert int(my_redis_client.get(f"{TEST_TOPIC}-available")) == 1
    redis_queue_client.register_infer_queue(TEST_TOPIC)
    assert int(my_redis_client.get(f"{TEST_TOPIC}-available")) == 2

def test_redis_infer_queue_client_unregister_infer_queue(redis_queue_client, my_redis_client):
    """Tests the unregister_infer_queue method of the RedisInferQueueClient class.

    This test checks if the unregister_infer_queue method can unregister the topic in Redis
    inference queue successfully.

    Args:
        redis_queue_client (RedisInferQueueClient): Fixture for RedisInferQueueClient.
        my_redis_client (Callable): Temporary redis client provided by pytest-redis's redisdb
          fixture.
    """
    redis_queue_client.register_infer_queue(TEST_TOPIC)
    redis_queue_client.register_infer_queue(TEST_TOPIC)
    redis_queue_client.unregister_infer_queue(TEST_TOPIC)
    assert int(my_redis_client.get(f"{TEST_TOPIC}-available")) == 1
    redis_queue_client.unregister_infer_queue(TEST_TOPIC)
    assert my_redis_client.exists(TEST_TOPIC) == 0

def test_redis_infer_queue_client_infer_queue_available(redis_queue_client):
    """Tests the infer_queue_available method of the RedisInferQueueClient class.

    This test checks if the infer_queue_available method can determine whether the topic in Redis
    inference queue is avaiable.

    Args:
        redis_queue_client (RedisInferQueueClient): Fixture for RedisInferQueueClient.
    """
    redis_queue_client.register_infer_queue(TEST_TOPIC)
    assert redis_queue_client.infer_queue_available(TEST_TOPIC)
    redis_queue_client.unregister_infer_queue(TEST_TOPIC)
    assert redis_queue_client.infer_queue_available(TEST_TOPIC) is False

def test_kafka_infer_queue_client_connect(kafka_queue_client):
    """Tests the connect method of the KafkaInferQueueClient class.

    This test checks if the connect method can connect to kafka server successfully.

    Args:
        kafka_queue_client (KafkaInferQueueClient): Fixture for KafkaInferQueueClient.
    """
    assert kafka_queue_client._conn.bootstrap_connected() # pylint: disable=protected-access

def test_kafka_infer_queue_client_connect_failed(kafka_broker):
    """Tests the connect method of the KafkaInferQueueClient class when the connection fails.

    Args:
        kafka_broker (Container): Fixture for kafka broker server.
    """
    KAFKA_PORT_WRONG = 9001
    broker_client = inferqueue.KafkaInferQueueClient()
    with pytest.raises(kafka.errors.NoBrokersAvailable):
        broker_client.connect(host=KAFKA_HOST, port=KAFKA_PORT_WRONG)

def test_kafka_infer_queue_client_publish_frame(kafka_queue_client, frame_instance):
    """Tests the publish_frame method of the KafkaInferQueueClient class.

    This test checks if the publish_frame method can publish frame to kafka server successfully.

    Args:
        kafka_queue_client (KafkaInferQueueClient): Fixture for KafkaInferQueueClient.
        frame_instance (Frame): Fixture for Frame.
    """
    consumer = KafkaConsumer(TEST_TOPIC, group_id='cnap-test-inferqueue',
                             bootstrap_servers=f"{KAFKA_HOST}:{KAFKA_PORT}",
                             auto_offset_reset='earliest', enable_auto_commit=False)
    assert consumer.bootstrap_connected()

    frame_blob = frame_instance.to_blob()
    kafka_queue_client.publish_frame(TEST_TOPIC, frame_blob)

    for message in consumer:
        assert message.value == frame_blob
        break

def test_invalid_topic(redis_queue_client, kafka_queue_client, frame_instance):
    """Tests the methods of infer queue client classes with invalid topic param.

    Args:
        redis_queue_client (RedisInferQueueClient): Fixture for RedisInferQueueClient.
        kafka_queue_client (KafkaInferQueueClient): Fixture for KafkaInferQueueClient.
        frame_instance (Frame): Fixture for Frame.
    """
    with pytest.raises(ValueError):
        redis_queue_client.publish_frame(None, frame_instance)
    with pytest.raises(ValueError):
        redis_queue_client.get_frame(None)
    with pytest.raises(ValueError):
        redis_queue_client.drop(None)
    with pytest.raises(ValueError):
        redis_queue_client.infer_queue_available(None)
    with pytest.raises(ValueError):
        redis_queue_client.register_infer_queue(None)
    with pytest.raises(ValueError):
        redis_queue_client.unregister_infer_queue(None)
    with pytest.raises(ValueError):
        kafka_queue_client.publish_frame(None, frame_instance)

def test_publish_frame_invalid_frame(redis_queue_client, kafka_queue_client):
    """Tests the publish_frame method with invalid frame.

    Args:
        redis_queue_client (RedisInferQueueClient): Fixture for RedisInferQueueClient.
        kafka_queue_client (KafkaInferQueueClient): Fixture for KafkaInferQueueClient.
    """
    with pytest.raises(ValueError):
        redis_queue_client.publish_frame(TEST_TOPIC, None)
    with pytest.raises(ValueError):
        kafka_queue_client.publish_frame(TEST_TOPIC, None)

def test_get_frame_empty_queue(redis_queue_client):
    """Tests the get_frame method when the infer queue is empty.

    Args:
        redis_queue_client (RedisInferQueueClient): Fixture for RedisInferQueueClient.
    """
    assert redis_queue_client.get_frame(TEST_TOPIC) is None
