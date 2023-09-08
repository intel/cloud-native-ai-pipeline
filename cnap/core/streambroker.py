"""A Streambroker module.

This module provides an object-oriented design for stream broker client to connect with
stream broker server, publish frame to stream broker server.

Classes:
    StreamBrokerClientBase: An abstract base class for stream broker client.
    RedisStreamBrokerClient: A concrete class implementing the StreamBrokerClientBase
      for Redis server.
    KafkaStreamBrokerClient: A concrete class implementing the StreamBrokerClientBase
      for Kafka server.
"""

import logging
from abc import ABC, abstractmethod
import time

import redis
from kafka import KafkaProducer
import kafka.errors
import cv2

from core.frame import Frame

# pylint: disable=no-member

LOG = logging.getLogger(__name__)

class StreamBrokerClientBase(ABC):
    """An abstract base class for stream broker client.

    This class serves as a blueprint for subclasses that need to implement
    `connect`, `publish_frame` methods for different types of stream broker
    server.
    """

    # The max reconnection times for stream broker client.
    MAX_RECONNECTION_TIMES = 5

    @abstractmethod
    def connect(self, host: str, port: int): # pragma: no cover
        """Connect to broker server.

        This method is used to connect to stream broker server, will attempt to reconnect
        when a connection error occcurs.

        Args:
            host (str): The host ip or hostname of broker server.
            port (str): The port of broker server.

        Raises:
            NotImplementedError: If the subclasses don't implement the method.
        """
        raise NotImplementedError("Subclasses should implement connect() method.")

    @abstractmethod
    def publish_frame(self, topic: str, frame: Frame) -> None: # pragma: no cover
        """Publish a frame to stream broker server for a topic.

        Args:
            topic (str): The topic name to publish to.
            frame (Frame): The Frame to publish.

        Raises:
            NotImplementedError: If the subclasses don't implement the method.
            ValueError: If the topic or frame is None.
            RuntimeError: If any errors while encoding before publishing frame.
        """
        raise NotImplementedError("Subclasses should implement publish_frame() method")


class RedisStreamBrokerClient(StreamBrokerClientBase):
    """Redis implementation for stream broker client.

    This class implement `connect`, `publish_frame` methods defined in
    `StreamBrokerClientBase` abstract base class for Redis stream broker.

    Attributes:
        _conn (redis.Redis): The Redis connection object.
    """

    def __init__(self):
        """Initialize a RedisStreamBrokerClient object.

        This constructor initializes the RedisStreamBrokerClient object with a
        Redis connection object.
        """
        self._conn = None

    def connect(self, host: str="127.0.0.1", port: int=6379):
        """Implement the `connect` method for the Redis stream broker client.

        The method overrides the `connect` method defined in `StreamBrokerClientBase`
        abstract base class.
        If connection to the Redis server fails and reconnection exceeds the limit,
        raise ConnectionError.

        Raises:
            redis.exceptions.ConnectionError: If connection to the Redis server fails
              and reconnection exceeds the limit.
        """
        self._conn = redis.Redis(host=host, port=port, db=0)

        sleep_time = 0.5

        # Attempts to reconnect when a connection error occurs, up to MAX_RECONNECTION_TIMES times,
        # so if a connection error still occurs on the (MAX_RECONNECTION_TIMES + 1)th loop,
        # raise conncection error
        for i in range(self.MAX_RECONNECTION_TIMES + 1):
            try:
                self._conn.ping()
            except redis.exceptions.ConnectionError as e:
                if i == self.MAX_RECONNECTION_TIMES:
                    LOG.error("Continuously reconnect to Redis server more than %d times",
                              self.MAX_RECONNECTION_TIMES)
                    raise redis.exceptions.ConnectionError(e) from e

                LOG.error("Failed to connect to Redis: %s", e)
                LOG.info("Reconnect to Redis server")

                # Sleep before reconnect, double the sleep time per reconnection.
                sleep_time *= 2

                time.sleep(sleep_time)

                # Connect to Redis server.
                self._conn = redis.Redis(host=host, port=port, db=0)

                # Connection is not successful, can not return.
                continue

            # If no connection error occurs, return directly.
            return

    def publish_frame(self, topic: str, frame: Frame) -> None:
        """See base class."""
        if topic is None:
            raise ValueError("topic can not be None")
        if frame is None:
            raise ValueError("frame can not be None")
        try:
            _, img = cv2.imencode('.jpg', frame.raw)
        except Exception as e:
            raise RuntimeError(f"Error during encoding image into jpg format: {str(e)}") from e
        frame.raw = img
        frame_blob = frame.to_blob()
        self._conn.publish(topic, frame_blob)


class KafkaStreamBrokerClient(StreamBrokerClientBase):
    """Kafka implementation for stream broker client.

    This class implement `connect`, `publish_frame` methods defined in
    `StreamBrokerClientBase` abstract base class for Kafka stream broker.

    Attributes:
        _conn (KafkaProducer): The Kafka connection object.
    """

    def __init__(self):
        """Initialize a KafkaStreamBrokerClient object.

        This constructor initializes the KafkaStreamBrokerClient object with a
        Kafka connection object.
        """
        self._conn = None

    def connect(self, host="127.0.0.1", port=9092):
        """Implement the `connect` method for the Kafka stream broker client.

        The method overrides the `connect` method defined in `StreamBrokerClientBase`
        abstract base class.
        If connection to the Kafka server fails and reconnection exceeds the limit,
        raise NoBrokersAvailable error.

        Raises:
            kafka.errors.NoBrokersAvailable: if connection to the Kafka server fails and
              reconnection exceeds the limit.
        """
        address = host + ":" + str(port)

        sleep_time = 0.5

        # Attempts to reconnect when a NoBrokersAvailable error occurs, up to MAX_RECONNECTION_TIMES
        # times, so if a NoBrokersAvailable error still occurs on the (MAX_RECONNECTION_TIMES + 1)th
        # loop, raise NoBrokersAvailable error
        for i in range(self.MAX_RECONNECTION_TIMES + 1):
            try:
                self._conn = KafkaProducer(bootstrap_servers=address)
            except kafka.errors.NoBrokersAvailable as e:
                if i == self.MAX_RECONNECTION_TIMES:
                    LOG.error("Continuously reconnect to Kafka server more than %d times",
                              self.MAX_RECONNECTION_TIMES)
                    raise kafka.errors.NoBrokersAvailable(e) from e

                LOG.error("Failed to connect to Kafka: %s", e)
                LOG.info("Reconnect to Kafka server")

                # Sleep before reconnect, double the sleep time per reconnection.
                sleep_time *= 2

                time.sleep(sleep_time)

                # Continue to reconnect to Kafka server
                continue

            # If no NoBrokersAvailable occurs, return directly.
            return

    def publish_frame(self, topic: str, frame: Frame) -> None:
        """See base class."""
        if topic is None:
            raise ValueError("topic can not be None")
        if frame is None:
            raise ValueError("frame can not be None")
        try:
            _, img = cv2.imencode('.jpg', frame.raw)
        except Exception as e:
            raise RuntimeError(f"Error during encoding image into jpg format: {str(e)}") from e
        frame.raw = img
        frame_blob = frame.to_blob()
        self._conn.send(topic, frame_blob)
