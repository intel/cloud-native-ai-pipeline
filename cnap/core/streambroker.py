"""
Package for stream broker client related classes. It provides client classes to
connect with stream broker server and publish frame to stream broker server.

The origin frames from streamprovider were inferenced by inferengine, then will
be published to stream broker, and then websocket server will fetch frame from
stream broker for next step action such as displaying on stream dashboard or
trigger Faas actions.

The `StreamBrokerClientBase` is the abstract class for stream broker client.
The `RedisStreamBrokerClient` and `KafkaStreamBrokerClient` are subclass for
Redis and Kafka stream broker server and can be extended to support other types
of stream broker by implementing other subclasses.
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

    """
    The Abstract class for stream broker client.
    """

    MAX_RECONNECTION_TIMES = 5

    @abstractmethod
    def connect(self, host: str, port: int) -> bool:
        """
        Connect to broker server.

        Args:
            host: The host ip of broker server.
            port: The port of broker server.

        Returns:
            bool: True if the connection is successful, False otherwise.
        """
        raise NotImplementedError("Subclasses should implement connect() method.")

    @abstractmethod
    def publish_frame(self, topic: str, frame: Frame) -> None:
        """
        Publish a frame to a topic.

        Args:
            topic: The topic name to publish to.
            frame: The frame to publish.

        Returns: None

        Raises:
            ValueError: if the topic or frame is None.
            RuntimeError: if any errors while encoding before publishing frame.
        """
        raise NotImplementedError("Subclasses should implement publish_frame() method")


class RedisStreamBrokerClient(StreamBrokerClientBase):

    """
    Redis implementation for stream broker client.
    """

    def __init__(self):
        self._conn = None

    def connect(self, host: str="127.0.0.1", port: int=6379):
        """
        Connect to Redis server, will attempt to reconnect when a connection error occcurs.

        Args:
            host: The host hostname/ip of Redis server.
            port: The port of Redis server.

        Returns: None

        Raises:
            redis.exceptions.ConnectionError: if connection to the Redis server fails
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
        if topic is None:
            raise ValueError("topic can not be None")
        if frame is None:
            raise ValueError("frame can not be None")
        try:
            _, img = cv2.imencode('.jpg', frame.raw)
        except Exception as e:
            raise RuntimeError(f"Error during encoding image into jpg format: {str(e)}") from e
        frame.raw = img
        try:
            frame_blob = frame.to_blob()
        except RuntimeError as e:
            raise RuntimeError(e) from e
        self._conn.publish(topic, frame_blob)


class KafkaStreamBrokerClient(StreamBrokerClientBase):

    """
    Kafka implementation for stream broker client.
    """

    def __init__(self):
        self._conn = None

    def connect(self, host="127.0.0.1", port=9092):
        """
        Connect to kafka server, will attempt to reconnect when a NoBrokersAvailable error occcurs.

        Args:
            host: The host hostname/ip of Kafka server.
            port: The port of Kafka server.

        Returns: None

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
        if topic is None:
            raise ValueError("topic can not be None")
        if frame is None:
            raise ValueError("frame can not be None")
        try:
            _, img = cv2.imencode('.jpg', frame.raw)
        except Exception as e:
            raise RuntimeError(f"Error during encoding image into jpg format: {str(e)}") from e
        frame.raw = img
        try:
            frame_blob = frame.to_blob()
        except RuntimeError as e:
            raise RuntimeError(e) from e
        self._conn.send(topic, frame_blob)
