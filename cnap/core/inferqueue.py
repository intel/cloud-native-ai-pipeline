"""
Package for inference queue client related classes. It provides client classes for
streaming service to connect with infer queue server and publish frame to infer
queue server, and for inference service to connect with infer queue server and get
frame from infer queue server and drop frames and adjust buffer size. The register
and unregister function for queue topic is provided to determine whether the topic
is available.

The origin frames from streamprovider will be send to infer queue server, and the
inference service can get frame from the infer queue server to do inference. The
infer queue provides a buffer between streaming service and inference service.

The `InferQueueClientBase` is the abstract class for infer queue server client.
The `RedisInferQueueClient` and `KafkaInferQueueClient` are subclass for Redis
and Kafka infer queue server(some functions of `KafkaInferQueueClient` is TODO now)
and can be extended to support other types of infer queue by implementing other subclasses.
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional
import time

import redis
from kafka import KafkaProducer
import kafka.errors

from core.frame import Frame

LOG = logging.getLogger(__name__)

class InferQueueClientBase(ABC):
    """
    Abstract class for inference queue client.
    """

    MAX_RECONNECTION_TIMES = 5

    def __init__(self):
        self._buffer_len = None

    @abstractmethod
    def connect(self, host: str, port: int):
        """
        Connect to queue server.

        Args:
            host: The host ip of queue server.
            port: The port of queue server.

        Returns: None
        """
        raise NotImplementedError("Subclasses should implement this")

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
        raise NotImplementedError("Subclasses should implement publish_frame() method.")

    @abstractmethod
    def get_frame(self, topic: str) -> Optional[Frame]:
        """
        Get a frame from queue.

        Args:
            topic: The topic name to get frame.

        Returns:
            Frame: The frame get from topic.
            None: The infer queue is empty now.

        Raises:
            ValueError: if the topic is None.
            TypeError: if the type of msg getted from infer queue is not bytes.
            RuntimeError: if any errors while decoding after getting frame.
        """
        raise NotImplementedError("Subclasses should implement get_frame() method.")

    @abstractmethod
    def drop(self, topic: str) -> int:
        """
        Drop the frame overflow the buffer.
        The length of buffer can be adjust.

        Args:
            topic: The topic name to drop frame.

        Returns:
            int: The count of frames dropped.

        Raises:
            ValueError: if the topic is None.
        """
        raise NotImplementedError("Subclasses should implement drop() method.")

    @property
    def buffer_len(self) -> int:
        """
        Get the buffer length for infer queue, default 32.
        """
        if self._buffer_len is None:
            self._buffer_len = 32
        return self._buffer_len

    @buffer_len.setter
    def buffer_len(self, new_buffer_len: int) -> None:
        """
        Set the buffer length for infer queue.
        """
        self._buffer_len = new_buffer_len

    @abstractmethod
    def infer_queue_available(self, topic: str) -> bool:
        """
        Determine whether the inference queue for the topic is available.

        Args:
            topic: The topic name to determine.

        Returns:
            bool: True if the inference queue for the topic is available, False otherwise.

        Raises:
            ValueError: if the topic is None.
        """
        raise NotImplementedError("Subclasses should implement infer_queue_available() method.")

    @abstractmethod
    def register_infer_queue(self, topic: str):
        """
        Register the topic in the inference queue.

        Args:
            topic: The topic name to register.

        Returns: None

        Raises:
            ValueError: if the topic is None.
        """
        raise NotImplementedError("Subclasses should implement register_infer_queue() method.")

    @abstractmethod
    def unregister_infer_queue(self, topic: str):
        """
        Unregister the topic in the inference queue.

        Args:
            topic: The topic name to unregister.

        Returns: None

        Raises:
            ValueError: if the topic is None.
        """
        raise NotImplementedError("Subclasses should implement unregister_infer_queue() method.")


class RedisInferQueueClient(InferQueueClientBase):
    """
    Redis implementation for inference queue client.
    """

    def __init__(self):
        InferQueueClientBase.__init__(self)
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
            frame_blob = frame.to_blob()
        except RuntimeError as e:
            raise RuntimeError(e) from e
        self._conn.rpush(topic, frame_blob)

    def get_frame(self, topic: str) -> Optional[Frame]:
        if topic is None:
            raise ValueError("topic can not be None")
        msg = self._conn.lpop(topic)
        if msg is None:
            return None
        try:
            return Frame.from_blob(msg)
        except TypeError as e:
            raise TypeError(e) from e
        except RuntimeError as e:
            raise RuntimeError(e) from e

    def drop(self, topic: str) -> int:
        if topic is None:
            raise ValueError("topic can not be None")
        queue_len = self._conn.llen(topic)
        drop_frame = 0
        if queue_len > self.buffer_len:
            self._conn.ltrim(topic, 0 - self.buffer_len, -1)
            drop_frame = queue_len - self.buffer_len
        return drop_frame

    def infer_queue_available(self, topic: str) -> bool:
        if topic is None:
            raise ValueError("topic can not be None")
        key = topic + "-available"
        return self._conn.exists(key)

    def register_infer_queue(self, topic: str):
        if topic is None:
            raise ValueError("topic can not be None")
        key = topic + "-available"
        if self._conn.exists(key):
            count = int(self._conn.get(key)) + 1
            self._conn.set(key, count)
        else:
            LOG.info("Register inference queue for topic: %s", topic)
            self._conn.set(key, 1)

    def unregister_infer_queue(self, topic: str):
        if topic is None:
            raise ValueError("topic can not be None")
        key = topic + "-available"
        count = int(self._conn.get(key)) - 1
        if count > 0:
            self._conn.set(key, count)
        else:
            LOG.info("Unregister inference queue for topic: %s", topic)
            self._conn.delete(key)
            self._conn.delete(topic)

class KafkaInferQueueClient(InferQueueClientBase):
    """
    Kafka implementation for inference queue client.
    """

    def __init__(self):
        InferQueueClientBase.__init__(self)
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
            frame_blob = frame.to_blob()
        except RuntimeError as e:
            raise RuntimeError(e) from e
        self._conn.send(topic, frame_blob)

    def get_frame(self, topic: str) -> Optional[Frame]:
        # TODO: implement the get_frame function for Kafka queue.
        return None

    def drop(self, topic: str) -> int:
        # TODO: implement the drop function for Kafka queue.
        return 0

    def infer_queue_available(self, topic: str) -> bool:
        # TODO: implement the infer_queue_available function for Kafka queue.
        return False

    def register_infer_queue(self, topic: str):
        # TODO: implement the register_infer_queue function for Kafka queue.
        return None

    def unregister_infer_queue(self, topic: str):
        # TODO: implement the unregister_infer_queue function for Kafka queue.
        return None
