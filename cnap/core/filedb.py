"""
This module provides an object-oriented design for file database to load video file.
It implements an abstract base class `FileDatabase` and a concrete filedatabase class
`LocalFileDatabase`.

`FileDatabase` serves as a blueprint for custom filedatabase implementations, while
`LocalFileDatabase` provide an implementation for local filedatabase to get video
file locally.

These classes can be easily extended or modified to accommodate new filedatabase type.
"""

import os
import logging
from abc import ABC, abstractmethod

LOG = logging.getLogger(__name__)

class FileDatabase(ABC):
    """
    Abstract base class for creating custom filedatabase implementations.
    """

    def __init__(self):
        pass

    @abstractmethod
    def get_file(self, filename: str) -> str:
        """
        Get/Download file from file database and return the local path for file.

        Args:
            filename: The name of file to get/Download.

        Returns:
            str: The local path for file.
        """
        raise NotImplementedError("Subclasses should implement get_file() method.")

class LocalFileDatabase(FileDatabase):
    """
    Local filedata base implementation for getting video file locally.
    """

    def __init__(self, root_dir: str):
        self._root_dir = os.path.abspath(root_dir)

    def get_file(self, filename: str) -> str:
        """
        Get the local path for file.

        Args:
            filename: The name of file to get.

        Returns:
            str: The local path for file.

        Raises:
            FileNotFoundError: if the root_dir is invalid or filed to find the given file.
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
