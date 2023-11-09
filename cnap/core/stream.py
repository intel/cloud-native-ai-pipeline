"""A Stream module.

This module provides an object-oriented design for Stream provider to provide stream input.

Classes:
    StreamProvider: An abstract base class for creating custom stream provider implementations.
    CameraSource: A concrete class implementing the StreamProvider for camera source.
    FileSource: A concrete class implementing the StreamProvider for file source.

functinos:
    create_stream_from_type: Create StreamProvider instance according to type.
"""

import os
import logging
import re
from typing import Tuple, Dict, Iterator, Any, Type
from abc import ABC, abstractmethod

import numpy
import cv2

from core.filedb import FileDatabase

# pylint: disable=no-member

LOG = logging.getLogger(__name__)

class StreamProvider(ABC):
    """An abstract base class for creating custom stream provider implementations.

    The class serves as a blueprint for subclasses that need to implement `verify`,
    `read_raw_frame`, `open`, `close` methods for different types of stream providers.

    Attributes:
        _name (str): The name of stream provider.
        _pathname (str): The path name of stream provider.
        _raw_size (Tuple[int, int]): The raw size (width, height) of frame captured from stream.
        _raw_fps (int): The raw FPS from source.
        _seq (int): The sequence of stream provider.
        _target_fps (int): The target FPS.
    """

    DEFAULT_WIDTH = 320
    DEFAULT_HEIGHT= 240
    DEFAULT_FPS = 15

    def __init__(self, name: str, pathname: str):
        """Initialize a StreamProvider object.

        This constructor initializes the StreamProvider with a given name and pathname.

        Args:
            name (str): The name of stream provider.
            pathname (str): The path name of stream provider.
        """
        self._name = name
        self._pathname = pathname
        self._raw_size = (self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT)
        self._raw_fps = self.DEFAULT_FPS
        self._seq = 0
        self._target_fps = -1

    @property
    def name(self) -> str:
        """str: The name of stream provider."""
        return self._name

    @property
    def pathname(self) -> str:
        """str: The path name of stream provider.

        For example:
        - Camera: "/dev/video0"
        - File: "SampleVideo.mp4"
        """
        return self._pathname

    @property
    def raw_size(self) -> Tuple[int, int]:
        """Tuple[int, int]: The raw size (width, height) of frame captured from stream."""
        return self._raw_size

    @property
    def raw_fps(self) -> int:
        """int: The raw FPS from source."""
        return self._raw_fps

    @property
    def target_fps(self) -> int:
        """int: The target FPS."""
        return self._target_fps

    @target_fps.setter
    def target_fps(self, new_val: int) -> None:
        """Set the target FPS."""
        self._target_fps = new_val

    @abstractmethod
    def verify(self) -> bool:
        """Verify the provider's measurement/quote/integrity.

        This method is used to verify the provider's measurement/quote/integrity.

        Returns:
            bool: True if the verification success, False otherwise.

        Raises:
            NotImplementedError: If the subclasses don't implement the method.
        """
        raise NotImplementedError("Subclasses should implement verify() method.")

    @abstractmethod
    def read_raw_frame(self) -> numpy.ndarray:
        """Get a frame from source.

        This method is used to get a frame from source.

        Returns:
            numpy.ndarray: An numpy.ndarray object representing the raw frame.

        Raises:
            NotImplementedError: If the subclasses don't implement the method.
        """
        raise NotImplementedError("Subclasses should implement read_raw_frame() method.")

    @abstractmethod
    def open(self) -> None:
        """Open the stream.

        The method is used to open the stream.

        Raises:
            NotImplementedError: If the subclasses don't implement the method.
        """
        raise NotImplementedError("Subclasses should implement open() method.")

    @abstractmethod
    def close(self) -> None:
        """Close the stream.

        The method is used to close the stream.

        Raises:
            NotImplementedError: If the subclasses don't implement the method.
        """
        raise NotImplementedError("Subclasses should implement close() method.")

    def __iter__(self) -> Iterator[Tuple[str, Any]]:
        """The Iterator for StreamProvider class."""
        yield 'name', self.name
        yield 'pathname', self.pathname
        yield 'size', self.raw_size
        yield 'fps', self.raw_fps


class CameraSource(StreamProvider):
    """A concrete class implementing the StreamProvider for camera source.

    This class implement `verify`, `read_raw_frame`, `open`, `close` methods defined
    in `StreamProvider` abstract base class for providing stream input from camera.

    Attributes:
        _device_obj (cv2.VideoCapture): The OpenCV VideoCapture object.
    """

    def __init__(self, name: str, pathname: str="/dev/video0"):
        """Initialize a CameraSource object.

        This constructor initializes the CameraSource with a given name and pathname.

        Args:
            name (str): The name of camera source stream provider.
            pathname (str): The path name of camera source stream provider.
        """
        StreamProvider.__init__(self, name, pathname)
        self._device_obj = None

    def _dev_num(self) -> int:
        """Get the number of device node.

        For example, it should be 0 for /dev/video0, and 1 for /dev/video1

        Returns:
            int: The number of device node.

        Raises:
            ValueError: If the stream path is None or is not a valid video device node.
            FileNotFoundError: If the camera's device node not exists.
        """
        if self.pathname is None:
            raise ValueError("Stream path name is None")
        if not re.match(r'/dev/video\d+', self.pathname):
            LOG.error("The pathname %s is not a valid video device node", self.pathname)
            raise ValueError(f"The pathname {self.pathname} is not a valid video device node")
        if not os.path.exists(self.pathname):
            LOG.error("The camera's device node %s not exists", self.pathname)
            raise FileNotFoundError(f"The camera's device node {self.pathname} not exists")
        return int(re.search(r'\d+', self.pathname).group())

    def verify(self) -> bool:
        """See base class."""
        return True

    def read_raw_frame(self) -> numpy.ndarray:
        """See base class."""
        ret, raw = self._device_obj.read()
        if ret:
            return raw
        return None

    def open(self):
        """Open the stream for camera source stream provider.

        The method override the `open` method defined in `StreamProvider` abstract base class.
        If the device node is not valid, or failed to open the camera, the method will raise
        ValueError or FileNotFoundError or IOError.

        Raises:
            ValueError: If the dev_num getted from path name is not valid.
            FileNotFoundError: If the path name for camera is not found.
            IOError: If failed to open the camera.
        """
        try:
            dev_num = self._dev_num()
        except ValueError as e:
            LOG.exception(e)
            raise ValueError(e) from e
        except FileNotFoundError as e:
            LOG.exception(e)
            raise FileNotFoundError(e) from e
        self._device_obj = cv2.VideoCapture(dev_num)
        if not self._device_obj.isOpened():
            LOG.error("Failed to open the camera, number: %d", dev_num)
            raise IOError(f"Failed to open the camera, number: {dev_num}")
        self._device_obj.set(cv2.CAP_PROP_FRAME_WIDTH, self.raw_size[0])
        self._device_obj.set(cv2.CAP_PROP_FRAME_HEIGHT, self.raw_size[1])
        self._device_obj.set(cv2.CAP_PROP_FPS, self.raw_fps)

    def close(self) -> None:
        """See base class."""
        if self._device_obj is not None:
            self._device_obj.release()


class FileSource(StreamProvider):
    """A concrete class implementing the StreamProvider for file source.

    This class implement `verify`, `read_raw_frame`, `open`, `close` methods defined
    in `StreamProvider` abstract base class for providing stream input from video file.

    Attributes:
        _file_db (FileDatabase): The file database of file source stream provider.
        _file_object (cv2.VideoCapture): The OpenCV VideoCapture object.
        _file_path (str): The video file path of file source stream provider.
        _frame_counter (int): The count of frames that have been read.
        _max_frame (int): The max frame count of file source stream provider.
    """

    DEFAULT_TARGET_FPS = 60

    def __init__(self, name: str, pathname: str="classroom.mp4"):
        """Initialize a FileSource object.

        This constructor initializes the FileSource with a given name and pathname.

        Args:
            name (str): The name of file source stream provider.
            pathname (str): The path name of file source stream provider.
        """
        StreamProvider.__init__(self, name, pathname)
        self._file_db = None
        self._file_object = None
        self._file_path = None
        self._frame_counter = 0
        self._max_frame = 0

    def verify(self) -> bool:
        """See base class."""
        return True

    def open(self):
        """Open the stream for file source stream provider.

        The method overrides the `open` method defined in `StreamProvider` abstract base class.
        If the file path is not valid, or failed to open the file, the method will raise
        FileNotFoundError or TypeError.

        Raises:
            FileNotFoundError: If the path name for video file is not found.
            TypeError: If failed to create the VideoCapture object.
        """
        LOG.debug("Open file source: %s", self._file_path)
        try:
            self._file_path = self.file_db.get_file(self.pathname)
        except FileNotFoundError as e:
            LOG.exception(e)
            raise FileNotFoundError(e) from e
        self._file_object = cv2.VideoCapture(self._file_path)
        if self._file_object is None:
            LOG.error("Failed to create VideoCapture object.")
            raise TypeError("Failed to create VideoCapture object.")
        self._max_frame = self._file_object.get(cv2.CAP_PROP_FRAME_COUNT)

    def close(self) -> None:
        """See base class."""
        LOG.debug("Close file source")
        if self._file_object is not None:
            self._file_object.release()

    def read_raw_frame(self) -> numpy.ndarray:
        """See base class."""
        ret, raw = self._file_object.read()
        if not ret:
            LOG.error("Failed to read video file.")
            return None
        self._frame_counter += 1

        # Reset the frame when finishing the video
        if self._frame_counter == self._max_frame:
            self._file_object.set(cv2.CAP_PROP_POS_FRAMES, 0)
            self._frame_counter = 0
        if raw is not None:
            raw = cv2.resize(raw, self.raw_size)
        return raw

    @property
    def file_db(self) -> FileDatabase:
        """FileDatabase: The file database of file source stream provider."""
        return self._file_db

    @file_db.setter
    def file_db(self, new_val: FileDatabase) -> None:
        """Set the file database for file source stream provider."""
        self._file_db = new_val

    @property
    def target_fps(self) -> int:
        """int: The target FPS of file source stream provider."""
        return self.DEFAULT_TARGET_FPS

    def __iter__(self) -> Iterator[Tuple[str, Any]]:
        """The Iterator for FileSource class."""
        yield 'name', self.name
        yield 'pathname', self.pathname
        yield 'size', self.raw_size
        yield 'fps', self.target_fps if self.target_fps != -1 else self.raw_fps

class StreamProcessor:
    """The class to process stream.

    Attributes:
        _provider (StreamProvider): The stream provider to process.
    """

    def __init__(self, provider: StreamProvider):
        """Initialize a StreamProcessor object.

        Args:
            provider (StreamProvider): The stream provider to process.
        """
        self._provider = provider

    @property
    def provider(self) -> StreamProvider:
        """StreamProvider: The provider instance."""
        return self._provider

    def prepare(self) -> None:
        """Prepare the stream processor.

        This function is used to prepare the stream processor, like verifying stream
        provider or registering the pipeline.
        """
        if not self._provider.verify():
            LOG.error("Failed to verify the provider")


PROVIDER_TYPES: Dict[str, Type[StreamProvider]] = {
    "camera": CameraSource,
    "file": FileSource
}

def create_stream_from_type(type_name: str, name: str, pathname: str) -> StreamProvider:
    """Create StreamProvider instance according to type.

    The method is used to create StreamProvider instance according to type.

    Args:
        type_name (str): The type of stream provider to create.
        name (str): The stream name of stream provider to create.
        pathname (str): The path name of stream provider to create.

    Returns:
        StreamProvider: The created stream provider.

    Raises:
        ValueError: If the provider source type is invalid.
    """
    if type_name not in PROVIDER_TYPES:
        LOG.error("Invalid provider source type")
        raise ValueError("Invalid provider source type")
    return PROVIDER_TYPES[type_name](name, pathname)
