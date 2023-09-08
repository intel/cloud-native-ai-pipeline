"""Conftest module.

This module contains the configurations for unit tests.

Functions:
    rtdb_connect: Fixture for Redis runtime database.
    docker_client: Fixture for docker client.
    network: Fixture for docker network.
    kafka_broker: Fixture for kafka broker server.
    img: Fixture for raw image.
    filesource: Fixture for file source stream provider.
    frame_instance: Fixture for Frame.
"""

import time
import os

import cv2
import pytest
from pytest_redis import factories
import docker

from cnap.core import frame, stream, rtdb

# pylint: disable=no-member
# pylint: disable=redefined-outer-name

CURR_DIR = os.path.dirname(os.path.abspath(__file__))

TEST_STREAM_NAME = 'classroom'
TEST_PIPELINE_ID = '2bbbdebe-3722-11ee-ba4a-d6bcdc58bce0'
TEST_FRAME_SEQUENCE = 0x5fffffffffff0000
TEST_FRAME_TIMESTAMP = 0.0

KAFKA_HOST = "localhost"
KAFKA_PORT = 9092
KAFKA_SERVER_START_TIME = 10

REDIS_HOST = "localhost"
REDIS_PORT = 8088

my_redis_server = factories.redis_proc(host=REDIS_HOST, port=REDIS_PORT)
my_redis_client = factories.redisdb('my_redis_server')

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

@pytest.fixture(scope="session")
def docker_client():
    """Fixture for docker client."""
    return docker.from_env()

@pytest.fixture(scope="session")
def network(docker_client):
    """Fixture for docker network."""
    _network = docker_client.networks.create(name="network-test")
    yield _network
    _network.remove()

@pytest.fixture(scope="session")
def kafka_broker(docker_client, network):
    """Fixture for kafka broker server."""
    broker_container = docker_client.containers.run(
        image="bitnami/kafka:latest",
        ports={
            f"{KAFKA_PORT}": f"{KAFKA_PORT}",
        },
        name="kafka-server",
        hostname=KAFKA_HOST,
        network=network.name,
        environment={
            "KAFKA_CFG_NODE_ID": 0,
            "KAFKA_CFG_PROCESS_ROLES": "controller,broker",
            "KAFKA_CFG_LISTENERS": f"PLAINTEXT://:{KAFKA_PORT},CONTROLLER://:{KAFKA_PORT + 1}",
            "KAFKA_CFG_LISTENER_SECURITY_PROTOCOL_MAP": "CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT",
            "KAFKA_CFG_CONTROLLER_QUORUM_VOTERS": f"0@kafka-server:{KAFKA_PORT + 1}",
            "KAFKA_CFG_CONTROLLER_LISTENER_NAMES": "CONTROLLER"
        },
        detach=True,
    )
    time.sleep(KAFKA_SERVER_START_TIME)
    yield broker_container
    broker_container.remove(force=True)

@pytest.fixture(scope="session")
def img():
    """Fixture for raw image.

    Returns:
        numpy.ndarray: The raw image for test.
    """
    img = cv2.imread(os.path.join(CURR_DIR, "../../docs/cnap_arch.png"))
    return img

@pytest.fixture(scope="session")
def filesource():
    """Fixture for file source stream provider.

    Returns:
        StreamProvider: A `StreamProvider` object instantiated as `FileSource`.
    """
    return stream.FileSource(TEST_STREAM_NAME)

@pytest.fixture
def frame_instance(filesource, img):
    """Fixture for Frame.

    Returns:
        Frame: A `Frame` object.
    """
    frame_instance = frame.Frame(filesource, TEST_PIPELINE_ID, TEST_FRAME_SEQUENCE, img)
    frame_instance.timestamp_new_frame = TEST_FRAME_TIMESTAMP
    return frame_instance
