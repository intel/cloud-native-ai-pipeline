"""Tests for the stream broker.

This module contains the tests for the stream broker.

Functions:
    redis_broker_client: Fixture for Redis Streambroker client.
    kafka_broker_client: Fixture for Kafka Streambroker client.
    test_redis_stream_broker_client_connect: Tests the connect method of the RedisStreamBrokerClient
      class.
    test_redis_stream_broker_client_connect_failed: Tests the connect method of the
      RedisStreamBrokerClient class when the connection fails.
    test_redis_stream_broker_client_publish_frame: Tests the publish_frame method of the
      RedisStreamBrokerClient class.
    test_kafka_stream_broker_client_connect: Tests the connect method of the KafkaStreamBrokerClient
      class.
    test_kafka_stream_broker_client_connect_failed: Tests the connect method of the
      KafkaStreamBrokerClient class when the connection fails.
    test_kafka_stream_broker_client_publish_frame: Tests the publish_frame method of the
      KafkaStreamBrokerClient class.
    test_publish_frame_invalid_topic: Tests the publish_frame method with invalid topic.
    test_publish_frame_invalid_frame: Tests the publish_frame method with invalid frame.
    test_publish_frame_error_encode: Tests the publish_frame method when encoding error.
"""

import pytest
import redis.exceptions
from kafka import KafkaConsumer
import kafka.errors
import cv2

from cnap.core import streambroker
from tests.core.conftest import TEST_PIPELINE_ID, KAFKA_HOST, KAFKA_PORT, REDIS_HOST, REDIS_PORT

TEST_TOPIC = f"result-{TEST_PIPELINE_ID}"

# pylint: disable=no-member
# pylint: disable=redefined-outer-name

@pytest.fixture(scope="module")
def redis_broker_client(my_redis_server):
    """Fixture for Redis Streambroker client.

    Args:
        my_redis_server (Callable): Temporary redis server provided by pytest-redis's redisdb
          fixture.

    Returns:
        RedisStreamBrokerClient: A `RedisStreamBrokerClient` object.
    """
    broker_conn = streambroker.RedisStreamBrokerClient()
    broker_conn.connect(host=REDIS_HOST, port=REDIS_PORT)
    return broker_conn

@pytest.fixture(scope="module")
def kafka_broker_client(kafka_broker):
    """Fixture for Kafka Streambroker client.

    Args:
        kafka_broker (Container): Fixture for kafka broker server.

    Returns:
        KafkaStreamBrokerClient: A `KafkaStreamBrokerClient` object.
    """
    broker_client = streambroker.KafkaStreamBrokerClient()
    broker_client.connect(host=KAFKA_HOST, port=KAFKA_PORT)
    return broker_client

def test_redis_stream_broker_client_connect(redis_broker_client):
    """Tests the connect method of the RedisStreamBrokerClient class.

    This test checks if the connect method can connect to redis server successfully.

    Args:
        redis_broker_client (RedisStreamBrokerClient): Fixture for RedisStreamBrokerClient.
    """
    assert redis_broker_client._conn.ping() # pylint: disable=protected-access

def test_redis_stream_broker_client_connect_failed(my_redis_server):
    """Tests the connect method of the RedisStreamBrokerClient class when the connection fails.

    Args:
        my_redis_server (Callable): Temporary redis server provided by pytest-redis's redisdb
          fixture.
    """
    REDIS_PORT_WRONG = 8001
    broker_client = streambroker.RedisStreamBrokerClient()
    with pytest.raises(redis.exceptions.ConnectionError):
        broker_client.connect(host=REDIS_HOST, port=REDIS_PORT_WRONG)

def test_redis_stream_broker_client_publish_frame(redis_broker_client, frame_instance,
                                                  my_redis_client):
    """Tests the publish_frame method of the RedisStreamBrokerClient class.

    This test checks if the publish_frame method can publish frame to redis server successfully.

    Args:
        redis_broker_client (RedisStreamBrokerClient): Fixture for RedisStreamBrokerClient.
        frame_instance (Frame): Fixture for Frame.
        my_redis_client (Callable): Temporary redis client provided by pytest-redis's redisdb
          fixture.
    """
    pubsub = my_redis_client.pubsub()
    pubsub.subscribe(TEST_TOPIC)
    response = pubsub.handle_message(pubsub.parse_response())
    assert response is not None and response['type'] == 'subscribe'

    redis_broker_client.publish_frame(TEST_TOPIC, frame_instance)

    response = pubsub.handle_message(pubsub.parse_response())
    assert response is not None and response['type'] == 'message'
    assert response['data'] == frame_instance.to_blob()

def test_kafka_stream_broker_client_connect(kafka_broker_client):
    """Tests the connect method of the KafkaStreamBrokerClient class.

    This test checks if the connect method can connect to redis server successfully.

    Args:
        kafka_broker_client (KafkaStreamBrokerClient): Fixture for KafkaStreamBrokerClient.
    """
    assert kafka_broker_client._conn.bootstrap_connected() # pylint: disable=protected-access

def test_kafka_stream_broker_client_connect_failed(kafka_broker):
    """Tests the connect method of the KafkaStreamBrokerClient class when the connection fails.

    Args:
        kafka_broker (Container): Fixture for kafka broker server.
    """
    KAFKA_PORT_WRONG = 9001
    broker_client = streambroker.KafkaStreamBrokerClient()
    with pytest.raises(kafka.errors.NoBrokersAvailable):
        broker_client.connect(host=KAFKA_HOST, port=KAFKA_PORT_WRONG)

def test_kafka_stream_broker_client_publish_frame(kafka_broker_client, frame_instance):
    """Tests the publish_frame method of the KafkaStreamBrokerClient class.

    This test checks if the publish_frame method can publish frame to kafka server successfully.

    Args:
        kafka_broker_client (KafkaStreamBrokerClient): Fixture for KafkaStreamBrokerClient.
        frame_instance (Frame): Fixture for Frame.
    """
    consumer = KafkaConsumer(TEST_TOPIC, group_id='test2',
                             bootstrap_servers=f"{KAFKA_HOST}:{KAFKA_PORT}",
                             auto_offset_reset='earliest', enable_auto_commit=False)
    assert consumer.bootstrap_connected()

    kafka_broker_client.publish_frame(TEST_TOPIC, frame_instance)

    for message in consumer:
        assert message.value == frame_instance.to_blob()
        break

def test_publish_frame_invalid_topic(redis_broker_client, kafka_broker_client, frame_instance):
    """Tests the publish_frame method with invalid topic.

    Args:
        redis_broker_client (RedisStreamBrokerClient): Fixture for RedisStreamBrokerClient.
        kafka_broker_client (KafkaStreamBrokerClient): Fixture for KafkaStreamBrokerClient.
        frame_instance (Frame): Fixture for Frame.
    """
    with pytest.raises(ValueError):
        redis_broker_client.publish_frame(None, frame_instance)
    with pytest.raises(ValueError):
        kafka_broker_client.publish_frame(None, frame_instance)

def test_publish_frame_invalid_frame(redis_broker_client, kafka_broker_client):
    """Tests the publish_frame method with invalid frame.

    Args:
        redis_broker_client (RedisStreamBrokerClient): Fixture for RedisStreamBrokerClient.
        kafka_broker_client (KafkaStreamBrokerClient): Fixture for KafkaStreamBrokerClient.
    """
    with pytest.raises(ValueError):
        redis_broker_client.publish_frame(TEST_TOPIC, None)
    with pytest.raises(ValueError):
        kafka_broker_client.publish_frame(TEST_TOPIC, None)

def test_publish_frame_error_encode(redis_broker_client, kafka_broker_client, frame_instance):
    """Tests the publish_frame method when encoding error.

    Args:
        redis_broker_client (RedisStreamBrokerClient): Fixture for RedisStreamBrokerClient.
        kafka_broker_client (KafkaStreamBrokerClient): Fixture for KafkaStreamBrokerClient.
        frame_instance (Frame): Fixture for Frame.
    """
    _, img = cv2.imencode('.jpg', frame_instance.raw)
    frame_instance.raw = img
    with pytest.raises(RuntimeError):
        redis_broker_client.publish_frame(TEST_TOPIC, frame_instance)
    with pytest.raises(RuntimeError):
        kafka_broker_client.publish_frame(TEST_TOPIC, frame_instance)
