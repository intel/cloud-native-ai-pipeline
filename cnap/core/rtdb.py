"""
Runtime Database (RTDB) is designed to cache the runtime information and
use an in-memory database service (like Redis,Kafka) as the backend
service.
An abstract class `RuntimeDatabaseBase` is defined as common abstract
methods to manage the tables, and class `RedisDB` is an implementation
for Redis backend service.
"""

import json
import logging

from abc import ABC, abstractmethod

import redis

LOG = logging.getLogger(__name__)

class RuntimeDatabaseBase(ABC):
    """
    Abstract base class to manage runtime database tables.
    """

    @abstractmethod
    def connect(self) -> bool:
        """
        Connect to the runtime database
        """
        raise NotImplementedError("Subclasses should implement this")

    @abstractmethod
    def save_table_object_dict(self, table: str, obj: str, d: dict) -> None:
        """
        Save a dict value for an object in a table
        """

    @abstractmethod
    def get_table_object_dict(self, table: str, obj: str) -> dict:
        """
        Get a dict value for an object from a table
        """

    @abstractmethod
    def get_all_table_objects_dict(self, table: str) -> dict:
        """
        Get all dict values from a table
        """

    @abstractmethod
    def check_table_object_exist(self, table: str, obj: str) -> bool:
        """
        Check whether given object exists in given table
        """

    @abstractmethod
    def del_table_object(self, table: str, obj: str) -> None:
        """
        Delete an object from a given table
        """

class RedisDB(RuntimeDatabaseBase):

    """
    Redis backend implementation for runtime database
    """

    def __init__(self):
        self._conn = None

    def connect(self, host: str = "127.0.0.1", port: int = 6379, db: int = 0) -> bool:
        """
        Connect to Redis server.
        Args:
            host: Redis server host hostname/IP
            port: Redis server port
            db: Database number in Redis server
        Returns:
            bool: Indicate whether connecting to the Redis server successfully
        """
        self._conn = redis.Redis(host=host, port=port, db=db)
        try:
            self._conn.ping()
        except redis.exceptions.ConnectionError:
            LOG.error("Failed to connect to Redis")
            return False
        return True

    def save_table_object_dict(self, table: str, obj: str, d: dict) -> None:
        """
        Save a dict value for an object in a table.
        Args:
            table: The name of the table
            obj: The name of the object
            d: The value to be saved
        Returns:
            None
        """
        LOG.debug("[Redis] Save => table: %s, obj: %s", table, obj)
        self._conn.hset(table, obj, json.dumps(d))

    def get_table_object_dict(self, table: str, obj: str) -> dict:
        """
        Get a dict value for an object from a table.
        Args:
            table: The name of the table
            obj: The name of the object
        Returns:
            dict: The value get by table name and object name
        """
        value = self._conn.hget(table, obj)
        if value is None:
            return {}
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            LOG.error("Invalid JSON value for table: %s, obj: %s", table, obj)
            return {}

    def get_all_table_objects_dict(self, table: str) -> dict:
        """
        Get all dict values from a table.
        Args:
            table: The name of the table
        Returns:
            dict: All values get by the table name
        """
        result_bytes = self._conn.hgetall(table)
        key_value_dict = {
            key.decode(): json.loads(value.decode())
            for key, value in result_bytes.items()
        }
        return key_value_dict

    def check_table_object_exist(self, table: str, obj: str) -> bool:
        """
        Check whether a given object exists in a given table.
        Args:
            table: The name of the table
            obj: The name of the object
        Returns:
            bool: Indicate whether a given object exists in a given table
        """
        return self._conn.hexists(table, obj)

    def del_table_object(self, table: str, obj: str) -> None:
        """
        Delete an object from a given table.
        Args:
            table: The name of the table
            obj: The name of the object
        Returns:
            None
        """
        self._conn.hdel(table, obj)
