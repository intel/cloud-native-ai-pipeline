"""A FileDatabase module.

This module provides an object-oriented design for a file database to load video files.

Classes:
    FileDatabase: An abstract base class for creating custom filedatabase implementations.
    LocalFileDatabase: A concrete class implementing the FileDatabase for local file operations.
"""

import os
import logging
from abc import ABC, abstractmethod

LOG = logging.getLogger(__name__)

class FileDatabase(ABC):
    """An abstract base class for creating custom file database implementations.

    This class serves as a blueprint for subclasses that need to implement
    the `get_file` method for different types of file databases.
    """

    @abstractmethod
    def __init__(self): # pragma: no cover
        """Initialize the FileDatabase object."""

    @abstractmethod
    def get_file(self, filename: str) -> str: # pragma: no cover
        """Abstract method for getting a file from the file database.

        This method is expected to retrieve a file from the file database and return
        the local path for the file.

        Args:
            filename (str): The name of the file to get.

        Returns:
            str: The local path for the file.

        Raises:
            NotImplementedError: if the subclass does not implement this method.
        """
        raise NotImplementedError("Subclasses should implement get_file() method.")

class LocalFileDatabase(FileDatabase):
    """A concrete class implementing the FileDatabase for local file operations.

    This class uses local filesystem to implement the `get_file` method
    defined in the `FileDatabase` abstract base class.

    Attributes:
        _root_dir (str): The root directory path for local file operations.
    """

    def __init__(self, root_dir: str):
        """Initializes the LocalFileDatabase with a given root directory.

        This constructor initializes the LocalFileDatabase with a given root directory
        for local file operations.

        Args:
            root_dir (str): The root directory path for local file operations.
        """
        self._root_dir = os.path.abspath(root_dir)

    def get_file(self, filename: str) -> str:
        """Gets the local path for a file.

        This method uses the root directory to find the given file and returns
        its local path.

        Args:
            filename (str): The name of the file to get.

        Returns:
            str: The local path for the file.

        Raises:
            FileNotFoundError: If the root_dir is invalid or failed to find the given file.
        """
        if not os.path.exists(self._root_dir):
            LOG.error("Invalid root directory for local file database.")
            raise FileNotFoundError("Invalid root directory for local file database.")

        filepath = os.path.join(self._root_dir, filename)
        if not os.path.exists(filepath):
            LOG.error("Failed to find the given file %s at %s",
                      filename, self._root_dir)
            raise FileNotFoundError(f"Failed to find the given file {filename} at {self._root_dir}")
        return filepath
