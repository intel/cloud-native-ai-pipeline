"""A Inferqueue module.

This module provides an object-oriented design for inference queue client to connect with
inference queue server, publish frame to queue server, get frame from queue server, drop
frames in queue server judge the availability for the topic in queue server, register topic
in queue server, unregister topic in queue server.

Classes:
    InferQueueClientBase: An abstract base class for inference queue client.
    RedisInferQueueClient: A concrete class implementing the InferQueueClientBase for Redis server.
    KafkaInferQueueClient: A concrete class implementing the InferQueueClientBase for Kafka server.
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional
import time

import redis
from kafka import KafkaProducer
import kafka.errors


LOG = logging.getLogger(__name__)

class InferQueueClientBase(ABC):
    """An abstract base class for inference queue client.

    This class serves as a blueprint for subclasses that need to implement
    `connect`, `publish_frame`, `get_frame`, `drop`, `infer_queue_available`,
    `register_infer_queue`, `unregister_infer_queue` methods for different types
    of queue server.

    Attributes:
        _buffer_len (int): The buffer length for inference queue.
    """

    # The max reconnection times for inference queue client.
    MAX_RECONNECTION_TIMES = 5

    def __init__(self):
        """Initialize a InferQueueClientBase object."""
        self._buffer_len = None

    @abstractmethod
    def connect(self, host: str, port: int): # pragma: no cover
        """Connect to queue server.

        This method is used to connect to queue server, will attempt to reconnect
        when a connection error occcurs.

        Args:
            host (str): The host ip or hostname of queue server.
            port (int): The port of queue server.

        Raises:
            NotImplementedError: If the subclasses don't implement the method.
        """
        raise NotImplementedError("Subclasses should implement connect() method.")

    @abstractmethod
    def publish_frame(self, topic: str, frame: bytes) -> None: # pragma: no cover
        """Publish a frame to queue server for a topic.

        This method is used to publish a frame to queue server, it will serialize
        the Frame before publish a frame to the queue server.

        Args:
            topic (str): The topic name to publish to.
            frame (bytes): The frame to publish.

        Raises:
            NotImplementedError: If the subclasses don't implement the method.
            ValueError: If the topic or frame is None.
        """
        raise NotImplementedError("Subclasses should implement publish_frame() method.")

    @abstractmethod
    def get_frame(self, topic: str) -> Optional[bytes]: # pragma: no cover
        """Get a frame from queue.

        This method is used to get a frame from queue server, it will deserialize
        the Frame after get a frame from the queue server,

        Args:
            topic (str): The topic name to get frame.

        Returns:
            Optional[bytes]: The frame get from topic or None if the infer queue is empty now.

        Raises:
            NotImplementedError: If the subclasses don't implement the method.
            ValueError: If the topic is None.
        """
        raise NotImplementedError("Subclasses should implement get_frame() method.")

    @abstractmethod
    def drop(self, topic: str) -> int: # pragma: no cover
        """Drop the frames overflow the buffer.

        This method is used to drop the frames overflow the buffer, the length
        of buffer can be adjusted.

        Args:
            topic (str): The topic name to drop frames.

        Returns:
            int: The count of frames dropped.

        Raises:
            NotImplementedError: If the subclasses don't implement the method.
            ValueError: If the topic is None.
        """
        raise NotImplementedError("Subclasses should implement drop() method.")

    @property
    def buffer_len(self) -> int:
        """int: The buffer length for infer queue, default 32."""
        if self._buffer_len is None:
            self._buffer_len = 32
        return self._buffer_len

    @buffer_len.setter
    def buffer_len(self, new_buffer_len: int) -> None:
        """Set the buffer length for infer queue."""
        self._buffer_len = new_buffer_len

    @abstractmethod
    def infer_queue_available(self, topic: str) -> bool: # pragma: no cover
        """Determine whether the inference queue for the topic is available.

        The method is used to determine whether the inference queue for the topic is available or
        not.

        Args:
            topic (str): The topic name to determine.

        Returns:
            bool: True if the inference queue for the topic is available, False otherwise.

        Raises:
            NotImplementedError: If the subclasses don't implement the method.
            ValueError: If the topic is None.
        """
        raise NotImplementedError("Subclasses should implement infer_queue_available() method.")

    @abstractmethod
    def register_infer_queue(self, topic: str): # pragma: no cover
        """Register the topic in the inference queue.

        The method is used to register the topic in the inference queue.

        Args:
            topic (str): The topic name to register.

        Raises:
            NotImplementedError: If the subclasses don't implement the method.
            ValueError: If the topic is None.
        """
        raise NotImplementedError("Subclasses should implement register_infer_queue() method.")

    @abstractmethod
    def unregister_infer_queue(self, topic: str): # pragma: no cover
        """Unregister the topic in the inference queue.

        The method is used to unregister the topic in the inference queue.

        Args:
            topic (str): The topic name to unregister.

        Raises:
            NotImplementedError: If the subclasses don't implement the method.
            ValueError: If the topic is None.
        """
        raise NotImplementedError("Subclasses should implement unregister_infer_queue() method.")


class RedisInferQueueClient(InferQueueClientBase):
    """Redis implementation for inference queue client.

    This class implement `connect`, `publish_frame`, `get_frame`, `drop`, `infer_queue_available`,
    `register_infer_queue`, `unregister_infer_queue` methods defined in `InferQueueClientBase`
    abstract base class for Redis queue server.

    Attributes:
        _conn (redis.Redis): The Redis connection object.
    """

    def __init__(self):
        """Initialize a RedisInferQueueClient object."""
        InferQueueClientBase.__init__(self)
        self._conn = None
        self._registered = False

    def connect(self, host: str="127.0.0.1", port: int=6379):
        """The Redis queue client implementation for connect method.

        The method overrides the `connect` method defined in the `InferQueueClientBase` abstract
        base class. The main defference is raises.

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

    def publish_frame(self, topic: str, frame: bytes) -> None:
        """See base class."""
        if topic is None:
            raise ValueError("topic can not be None")
        if frame is None:
            raise ValueError("frame can not be None")
        self._conn.rpush(topic, frame)

    def get_frame(self, topic: str) -> Optional[bytes]:
        """See base class."""
        if topic is None:
            raise ValueError("topic can not be None")
        msg = self._conn.lpop(topic)
        if msg is None:
            return None
        return msg

    def drop(self, topic: str) -> int:
        """See base class."""
        if topic is None:
            raise ValueError("topic can not be None")
        queue_len = self._conn.llen(topic)
        drop_frame = 0
        if queue_len > self.buffer_len:
            self._conn.ltrim(topic, 0 - self.buffer_len, -1)
            drop_frame = queue_len - self.buffer_len
        return drop_frame

    def infer_queue_available(self, topic: str) -> bool:
        """See base class."""
        if topic is None:
            raise ValueError("topic can not be None")
        key = topic + "-available"
        return int(self._conn.get(key)) > 0

    def register_infer_queue(self, topic: str):
        """See base class."""
        if topic is None:
            raise ValueError("topic can not be None")
        key = topic + "-available"
        if self._conn.incr(key) == 1:
            LOG.info("Register inference queue for topic: %s", topic)
        self._registered = True

    def unregister_infer_queue(self, topic: str):
        """See base class."""
        if topic is None:
            raise ValueError("topic can not be None")
        if not self._registered:
            return
        key = topic + "-available"
        if self._conn.decr(key) == 0:
            LOG.info("Unregister inference queue for topic: %s", topic)
            self._conn.delete(topic)

class KafkaInferQueueClient(InferQueueClientBase):
    """Kafka implementation for inference queue client.

    This class implement `connect`, `publish_frame`, `get_frame`, `drop`, `infer_queue_available`,
    `register_infer_queue`, `unregister_infer_queue` methods defined in `InferQueueClientBase`
    abstract base class for Kafka queue server.

    Attributes:
        _conn (KafkaProducer): The Kafka producer connection object.
    """

    def __init__(self):
        """Initialize a KafkaInferQueueClient object."""
        InferQueueClientBase.__init__(self)
        self._conn = None

    def connect(self, host="127.0.0.1", port=9092):
        """The Kafka queue client implementation for connect method.

        The method overrides the `connect` method defined in the `InferQueueClientBase` abstract
        base class. The main defference is raises.

        Raises:
            kafka.errors.NoBrokersAvailable: If connection to the Kafka server fails and
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

    def publish_frame(self, topic: str, frame: bytes) -> None:
        """See base class."""
        if topic is None:
            raise ValueError("topic can not be None")
        if frame is None:
            raise ValueError("frame can not be None")
        self._conn.send(topic, frame)

    def get_frame(self, topic: str) -> Optional[bytes]: # pragma: no cover
        """See base class."""
        # TODO: implement the get_frame function for Kafka queue.
        return None

    def drop(self, topic: str) -> int: # pragma: no cover
        """See base class."""
        # TODO: implement the drop function for Kafka queue.
        return 0

    def infer_queue_available(self, topic: str) -> bool: # pragma: no cover
        """See base class."""
        # TODO: implement the infer_queue_available function for Kafka queue.
        return False

    def register_infer_queue(self, topic: str): # pragma: no cover
        """See base class."""
        # TODO: implement the register_infer_queue function for Kafka queue.
        return None

    def unregister_infer_queue(self, topic: str): # pragma: no cover
        """See base class."""
        # TODO: implement the unregister_infer_queue function for Kafka queue.
        return None
