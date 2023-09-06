"""A RuntimeDatabase module.

This module provides an object-oriented design for Runtime Database to cache the
runtime information and use in-memory datbase services (like Redis) as backend service.

Classes:
    RuntimeDatabaseBase: An abstract base class to manage runtime database tables.
    RedisDB:  A concrete class implementing the RuntimeDatabaseBase using Redis as backend service.
"""

import json
import logging
import time

from abc import ABC, abstractmethod

import redis

LOG = logging.getLogger(__name__)

class RuntimeDatabaseBase(ABC):
    """An abstract base class to manage runtime database tables.

    This class serves as a blutprint for subclasses that need to implement `connect`,
    `save_table_object_dict`, `get_table_object_dict`, `get_all_table_objects_dict`,
    `check_table_object_exist`, `del_table_object` methods for different types of
    in-memory database services.
    """

    # The max reconnection times for runtime database.
    MAX_RECONNECTION_TIMES = 5

    @abstractmethod
    def connect(self, host: str, port: int): # pragma: no cover
        """Connect to runtime database.

        This method is used to connect to runtime database, will attempt to reconnect
        when a connection error occcurs.

        Args:
            host (str): The host ip or hostname of runtime database.
            port (int): The port of runtime database.

        Raises:
            NotImplementedError: If the subclasses don't implement the method.
        """
        raise NotImplementedError("Subclasses should implement connect() method.")

    @abstractmethod
    def save_table_object_dict(self, table: str, obj: str, d: dict) -> None: # pragma: no cover
        """Save a dict value for an object in a table.

        This method is used to save a dict value for an object in a table.

        Args:
            table (str): The name of the table.
            obj (str): The name of the object.
            d (dict): The value to be saved.

        Raises:
            NotImplementedError: If the subclasses don't implement the method.
            ValueError: If `table` or `obj` is None.
        """
        raise NotImplementedError("Subclasses should implement save_table_object_dict() method.")

    @abstractmethod
    def get_table_object_dict(self, table: str, obj: str) -> dict: # pragma: no cover
        """Get a dict value for an object from a table.

        This method is used to get a dict value for an object from a table.

        Args:
            table (str): The name of the table.
            obj (str): The name of the object.

        Returns:
            dict: The dict value get by table name and object name.

        Raises:
            NotImplementedError: If the subclasses don't implement the method.
            ValueError: If `table` or `obj` is None.
        """
        raise NotImplementedError("Subclasses should implement get_table_object_dict() method.")

    @abstractmethod
    def get_all_table_objects_dict(self, table: str) -> dict: # pragma: no cover
        """Get all dict values from a table.

        This method is used to get all dict values from a table.

        Args:
            table (str): The name of the table.

        Returns:
            dict: All dict values get by the table name.

        Raises:
            NotImplementedError: If the subclasses don't implement the method.
            ValueError: If `table` is None.
        """
        raise NotImplementedError("Subclasses should implement get_all_table_objects_dict() \
                                  method.")

    @abstractmethod
    def check_table_object_exist(self, table: str, obj: str) -> bool: # pragma: no cover
        """Check whether a given object exists in a given table.

        This method is used to check whether a given object exists in a given table.

        Args:
            table (str): The name of the table.
            obj (str): The name of the object.

        Returns:
            bool: True if a given object exists in a given table, otherwise False.

        Raises:
            NotImplementedError: If the subclasses don't implement the method.
            ValueError: If `table` or `obj` is None.
        """
        raise NotImplementedError("Subclasses should implement check_table_object_exist() method.")

    @abstractmethod
    def del_table_object(self, table: str, obj: str) -> None: # pragma: no cover
        """Delete an object from a given table.

        This method is used to delete an object from a given table.

        Args:
            table (str): The name of the table.
            obj (str): The name of the object.

        Raises:
            NotImplementedError: If the subclasses don't implement the method.
            ValueError: If `table` or `obj` is None.
        """
        raise NotImplementedError("Subclasses should implement del_table_object() method.")

class RedisDB(RuntimeDatabaseBase):
    """Redis backend implementation for runtime database.

    This class implements `connect`, `save_table_object_dict`, `get_table_object_dict`,
    `get_all_table_objects_dict`, `check_table_object_exist`, `del_table_object` methods
    defined in `RuntimeDatabaseBase` abstract base class for Redis in-memory datbase backend.

    Attributes:
        _conn (redis.Redis): The Redis connection object.
    """

    def __init__(self):
        """Initialize a RedisDB object."""
        self._conn = None

    def connect(self, host: str = "127.0.0.1", port: int = 6379, db: int = 0) -> None:
        """The connect method for the runtime database of Redis backend implementation.

        The method overrides the `connect` method defined in the `RuntimeDatabaseBase` abstract
        base class. The main difference is raises.

        Raises:
            redis.exceptions.ConnectionError: If connection to the Redis server fails
              and reconnection exceeds the limit.
        """
        self._conn = redis.Redis(host=host, port=port, db=db)

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

    def save_table_object_dict(self, table: str, obj: str, d: dict) -> None:
        """See base class."""
        if table is None:
            raise ValueError("table name cannot be None")

        if obj is None:
            raise ValueError("object cannot be None")

        try:
            json_value = json.dumps(d)
        except TypeError as e:
            LOG.error("Failed to serialize value into JSON: %s", str(d))
            raise e

        LOG.debug("[Redis] Save => table: %s, obj: %s", table, obj)
        self._conn.hset(table, obj, json_value)

    def get_table_object_dict(self, table: str, obj: str) -> dict:
        """See base class."""
        if table is None:
            raise ValueError("table name cannot be None")

        if obj is None:
            raise ValueError("object cannot be None")

        value = self._conn.hget(table, obj)
        if value is None:
            return {}
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            LOG.error("Invalid JSON value for table: %s, obj: %s", table, obj)
            return {}

    def get_all_table_objects_dict(self, table: str) -> dict:
        """See base class."""
        if table is None:
            raise ValueError("table name cannot be None")

        result_bytes = self._conn.hgetall(table)
        if not result_bytes:
            return {}

        key_value_dict = {}
        for key, value in result_bytes.items():
            try:
                key_value_dict[key.decode()] = json.loads(value.decode())
            except json.JSONDecodeError:
                LOG.error("Invalid JSON value for table: %s, key: %s", table, key.decode())

        return key_value_dict

    def check_table_object_exist(self, table: str, obj: str) -> bool:
        """See base class."""
        if table is None:
            raise ValueError("table name cannot be None")

        if obj is None:
            raise ValueError("object cannot be None")

        return self._conn.hexists(table, obj)

    def del_table_object(self, table: str, obj: str) -> None:
        """See base class."""
        if table is None:
            raise ValueError("table name cannot be None")

        if obj is None:
            raise ValueError("object cannot be None")

        self._conn.hdel(table, obj)
