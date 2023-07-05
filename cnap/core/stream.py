"""
This module provides an object-oriented design for Stream provider to provide stream input.
It implement an abstract base class `StreamProvider` and two concrete stream provider classes
`CameraSource` and `FileSource`. It also provides a `StreamProcessor` class to process stream
and provides a `create_stream_from_type` function to create StreamProvider instance according
to type. 

`StreamProvider` serves as a blueprint for custom stream provider implementations, while
`CameraSource` provides an implementation to provide stream input from camera, and `FileSource`
provides an implementation to provide stream input from video file.

These classes can be easily extended or modified to accommodate new stream provider.
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
    """
    Abstract base class for creating custom stream provider implementations.
    """

    DEFAULT_WIDTH = 320
    DEFAULT_HEIGHT= 240
    DEFAULT_FPS = 15

    def __init__(self, name: str, pathname: str):
        """
        Initialize a StreamProvider object.

        Args:
            name: The name of stream provider.
            pathname: The path name of stream provider.
        """
        self._name = name
        self._pathname = pathname
        self._raw_size = (self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT)
        self._raw_fps = self.DEFAULT_FPS
        self._seq = 0
        self._target_fps = -1

    @property
    def name(self) -> str:
        """
        Get the stream Name.
        """
        return self._name

    @property
    def pathname(self) -> str:
        """
        Get the stream Path Name, for example:
        - Camera: "/dev/video0"
        - File: "SampleVideo.mp4"
        """
        return self._pathname

    @property
    def raw_size(self) -> Tuple[int, int]:
        """
        Get the raw size (width, height) of frame captured from stream.
        """
        return self._raw_size

    @property
    def raw_fps(self) -> int:
        """
        Get the raw FPS from source.
        """
        return self._raw_fps

    @property
    def target_fps(self) -> int:
        """
        Get the target FPS.
        """
        return self._target_fps

    @target_fps.setter
    def target_fps(self, new_val: int) -> None:
        """
        Set the target FPS.
        """
        self._target_fps = new_val

    @abstractmethod
    def verify(self) -> bool:
        """
        Verify the provider's measurement/quote/integrity.

        Returns:
            bool: True if the verification success, False otherwise.
        """
        raise NotImplementedError("Subclasses should implement verify() method.")

    @abstractmethod
    def read_raw_frame(self) -> numpy.ndarray:
        """
        Get a frame from source.

        Returns:
            numpy.ndarray: An numpy.ndarray object representing the raw frame.
        """
        raise NotImplementedError("Subclasses should implement read_raw_frame() method.")

    @abstractmethod
    def open(self) -> None:
        """
        Open the stream.

        Return: None
        """
        raise NotImplementedError("Subclasses should implement open() method.")

    @abstractmethod
    def close(self) -> None:
        """
        Close the stream.

        Return: None
        """
        raise NotImplementedError("Subclasses should implement close() method.")

    def __iter__(self) -> Iterator[Tuple[str, Any]]:
        yield 'name', self.name
        yield 'pathname', self.pathname
        yield 'size', self.raw_size
        yield 'fps', self.raw_fps


class CameraSource(StreamProvider):
    """
    Camera Source stream provider implementation for providing stream input from camera.
    """

    def __init__(self, name: str, pathname: str="/dev/video0"):
        """
        Initialize a CameraSource object.

        Args:
            name: The name of camera source stream provider.
            pathname: The path name of camera source stream provider.
        """
        StreamProvider.__init__(self, name, pathname)
        self._device_obj = None

    def _dev_num(self) -> int:
        """
        Get the number of device node.

        For example, it should be 0 for /dev/video0, and 1 for /dev/video1

        Returns:
            int: The number of device node.

        Raises:
            ValueError: if the stream path is None or is not a valid video device node.
            FileNotFoundError: if the camera's device node not exists.
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
        return True

    def read_raw_frame(self) -> numpy.ndarray:
        ret, raw = self._device_obj.read()
        if ret:
            return raw
        return None

    def open(self):
        """
        Open the stream for camera source stream provider.

        Return: None

        Raises:
            ValueError: if the dev_num getted from path name is not valid.
            FileNotFoundError: if the path name for camera is not found.
            IOError: if failed to open the camera.
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
        if self._device_obj is not None:
            self._device_obj.release()


class FileSource(StreamProvider):
    """
    File source stream provider implementation for providing stream input from video file.
    """

    DEFAULT_TARGET_FPS = 25

    def __init__(self, name: str, pathname: str="classroom.mp4"):
        """
        Initialize a FileSource object.

        Args:
            name: The name of file source stream provider.
            pathname: The path name of file source stream provider.
        """
        StreamProvider.__init__(self, name, pathname)
        self._file_db = None
        self._file_object = None
        self._file_path = None
        self._frame_counter = 0
        self._max_frame = 0

    def verify(self) -> bool:
        return True

    def open(self):
        """
        Open the stream for file source stream provider.

        Return: None

        Raises:
            FileNotFoundError: if the path name for video file is not found.
            TypeError: if failed to create the VideoCapture object.
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
        LOG.debug("Close file source")
        if self._file_object is not None:
            self._file_object.release()

    def read_raw_frame(self) -> numpy.ndarray:
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
        """
        Get the file database.
        """
        return self._file_db

    @file_db.setter
    def file_db(self, new_val: FileDatabase) -> None:
        """
        Set the file database.
        """
        self._file_db = new_val

    @property
    def target_fps(self) -> int:
        """
        Get the target FPS.
        """
        return self.DEFAULT_TARGET_FPS

class StreamProcessor:
    """
    The class to process stream.
    """

    def __init__(self, provider: StreamProvider):
        """
        Initialize a StreamProcessor object.

        Args:
            provider(StreamProvider): The stream provider to process.
        """
        self._provider = provider

    @property
    def provider(self) -> StreamProvider:
        """
        Get the provider instance.
        """
        return self._provider

    def prepare(self) -> None:
        """
        Prepare the stream processor like verifying stream provider or registering the pipeline.
        """
        if not self._provider.verify():
            LOG.error("Failed to verify the provider")


PROVIDER_TYPES: Dict[str, Type[StreamProvider]] = {
    "camera": CameraSource,
    "file": FileSource
}

def create_stream_from_type(type_name: str, name: str, pathname: str) -> StreamProvider:
    """
    Create StreamProvider instance according to type.

    Args:
        type_name: The type of stream provider to create.
        name: The stream name of stream provider to create.
        pathname: The path name of stream provider to create.

    Returns:
        StreamProvider: The created stream provider.

    Raises:
        ValueError: if the provider source type is invalid.
    """
    if type_name not in PROVIDER_TYPES:
        LOG.error("Invalid provider source type")
        raise ValueError("Invalid provider source type")
    return PROVIDER_TYPES[type_name](name, pathname)
