"""A Zip module.

This module provides a class to compress/decompress of frames.

Classes:
    ZipBase: An abstract base class for creating custom zip implementations.
    CPUZip: A concrete class implementing compress and decompress frame with CPU.
"""
import gzip
import time
import logging
from abc import ABC, abstractmethod
LOG = logging.getLogger(__name__)

class ZipBase(ABC):
    """An Abstract base class for creating custom zip implementations.

    This class serves as a blueprint for subclass that need to implement `compress`
    and `decompress` method for different accelerators.
    """

    def __init__(self):
        """Initialize a ZipBase object."""

    def __del__(self):
        """Destroy a ZipBase object."""

    @abstractmethod
    def compress(self, src: bytes) -> bytes:
        """Compress.

        The method is to compress frame.
        
        Args:
            src (bytes): Frame that need to be compressed.

        Returns:
            bytes: Compressed Frame.

        Raises:
            NotImplementedError: If the subclasses don't implement the method.
            OverflowError: If compression integer overflow occurs.
            ValueError: If the compression input length is invalid.
            RuntimeError: If any error occurs during compression.
        """
        raise NotImplementedError("Subclasses should implement connect() method.")

    @abstractmethod
    def decompress(self, src: bytes) -> bytes:
        """Decompress.

        The method is to decompress frame.
        
        Args:
            src (bytes): Frame that need to be decompressed.

        Returns:
            bytes: Decompressed Frame.

        Raises:
            NotImplementedError: If the subclasses don't implement the method.
            RuntimeError: If any error occurs during decompression
        """
        raise NotImplementedError("Subclasses should implement connect() method.")


class CPUZip(ZipBase):
    """A class that use CPU to compress and decompress."""

    def __init__(self):
        """Initialize a CPUZip object."""

    def __del__(self):
        """Destroy a CPUZip object."""

    def compress(self, src: bytes) -> bytes:
        """See base class."""
        start_time = time.time()
        #use gzip to compress
        dst =gzip.compress(src)

        end_time= time.time()
        time_cost = end_time -start_time
        LOG.debug("compress %d bytes in %d bytes, cost %fs", len(src), len(dst), time_cost)
        return dst

    def decompress(self, src: bytes) -> bytes:
        """See base class."""
        start_time = time.time()
        #use gzip to decompress
        dst =gzip.decompress(src)

        end_time= time.time()
        time_cost = end_time - start_time
        LOG.debug("decompress %d bytes in %d bytes, cost %fs", len(src), len(dst), time_cost)
        return dst
