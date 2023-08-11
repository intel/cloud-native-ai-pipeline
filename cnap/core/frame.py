"""A Frame module.

This module contains the definition of frame class, which encapsulates raw frame and related
information for transferring data between micro services, it can be simply encoded and decoded
by protobuf. A frame should include enough information for traceability, observability, etc.

In addition, this module provides an object-oriented design for frame cipher to encrypt and
decrypt frame.

Classes:
    Frame: A class that encapsulates raw frame and related information, can be simply encoded and
      decoded by protobuf.
    FrameCipherBase: An abstract base class for creating custom frame cipher implementations.
    QATFrameCipher: A concrete class implementing encrypt and decrypt frame accelerated with QAT.
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Tuple

import numpy as np
import cv2

from core.stream import StreamProvider
from core.generated.core.protobuf import frame_pb2

LOG = logging.getLogger(__name__)

# pylint: disable=no-member

class FrameCipherBase(ABC):
    """An Abstract base class for creating custom frame cipher implementations.

    This class serves as a blueprint for subclass that need to implement `encrypt`
    and `decrypt` method for different accelerators.
    """

    @abstractmethod
    def encrypt(self) -> None:
        """Encrypt the frame.

        The method is to encrypt the frame to protect the privacy of the frame.

        Raises:
            NotImplementedError: If the subclasses don't implement the method.
        """
        raise NotImplementedError("Subclasses should implement encrypt() method.")

    @abstractmethod
    def decrypt(self) -> None:
        """Decrypt the frame.

        The method is to decrypt the encrypted frame.

        Raises:
            NotImplementedError: If the subclasses don't implement the method.
        """
        raise NotImplementedError("Subclasses should implement decrypt method.")

class Frame:
    """A class that encapsulates raw frame and related information.

    The Frame include enough information for traceability, observability, and
    can be simply encoded and decoded by protobuf.

    Attributes:
        _provider (StreamProvider): The stream provider of the frame.
        _pipeline_id (str): The id of the pipeline to which the frame belongs.
        _sequence (int): The monolithic counter of the frame sequence number.
        _raw (np.ndarray): The raw frame of the frame.
        _ts_new (float): The timestamp of the beginning of this new frame.
        _ts_infer_start (float): The timestamp of the inference's start point of this frame.
    """

    # Class variable to calculate the last sequence number
    last_sequence = 0

    def __init__(self, provider: StreamProvider, pipeline_id: str,
                 sequence: int, raw_frame: np.ndarray):
        """Initialize a Frame object.

        This constructor initializes a Frame object with the given stream provider,
        pipeline id, sequence number and raw frame.

        Args:
            provider (StreamProvider): The stream provider of the frame.
            pipeline_id (str): The pipeline id of the frame.
            sequence (int): The initial sequence number of the frame.
            raw_frame (np.ndarray): The raw frame of the frame.
        """
        self._provider = provider
        self._pipeline_id = pipeline_id
        self._sequence = sequence
        self._raw = raw_frame
        self._ts_new = time.time()
        self._ts_infer_start = 0

    @property
    def pipeline_id(self) -> str:
        """str: The id of the pipeline to which the frame belongs."""
        return self._pipeline_id

    @pipeline_id.setter
    def pipeline_id(self, new_str: str) -> None:
        """Set pipeline ID from string."""
        self._pipeline_id = new_str

    @property
    def sequence(self) -> int:
        """int: The monolithic counter of the frame sequence number."""
        return self._sequence

    @property
    def timestamp_new_frame(self) -> float:
        """float: The timestamp of the beginning of this new frame."""
        return self._ts_new

    @timestamp_new_frame.setter
    def timestamp_new_frame(self, timestamp: float) -> None:
        """Set the timestamp of the beginning of this new frame."""
        self._ts_new = timestamp

    @property
    def raw(self) -> np.ndarray:
        """np.ndarray: The raw frame of the frame."""
        return self._raw

    @raw.setter
    def raw(self, raw_frame: np.ndarray) -> None:
        """Set raw frame raw data."""
        self._raw = raw_frame

    @property
    def timestamp_infer_start(self) -> float:
        """float: The timestamp of the inference's start point of this frame."""
        return self._ts_infer_start

    @timestamp_infer_start.setter
    def timestamp_infer_start(self, timestamp: float) -> None:
        """Set the timestamp of the inference's start point."""
        self._ts_infer_start = timestamp

    def to_blob(self) -> bytes:
        """Encode the raw frame to a blob for transferring to the infer queue.

        This method uses protobuf to serialize a Frame into a blob.

        Returns:
            bytes: The blob encoded from raw frame.

        Raises:
            RuntimeError: If any errors while encoding.
        """
        try:
            # Get the frame shape info
            if len(self._raw.shape) == 3:
                height, width, channel = self._raw.shape
            elif len(self._raw.shape) == 2:
                height, width = self._raw.shape
                channel = 1
            else:
                height, width, channel = 1, len(self._raw), 1

            frame_msg = frame_pb2.FrameMessage()
            frame_msg.pipeline_id = self._pipeline_id
            frame_msg.sequence = self._sequence
            frame_msg.raw = self._raw.tobytes()
            frame_msg.ts_new = self._ts_new
            frame_msg.raw_height = height
            frame_msg.raw_width = width
            frame_msg.raw_channels = channel
            frame_msg.ts_infer_start = self._ts_infer_start

            serialized_data = frame_msg.SerializeToString()
            # TODO: zlib, gzip or QATZip to accelerate the compression
            compressed_data = serialized_data

            return compressed_data
        except Exception as e:
            raise RuntimeError(f"Error during encoding frame: {str(e)}") from e

    @staticmethod
    def from_blob(blob: bytes) -> 'Frame':
        """Restore a frame instance from a blob.

        This method uses protobuf to deserialize a blob to a Frame.

        Args:
            blob (bytes): The blob to restore.

        Returns:
            Frame: The frame restored from a blob.

        Raises:
            TypeError: If the type of 'blob' argument is not bytes type.
            RuntimeError: If any errors while decoding.
        """
        if not isinstance(blob, bytes):
            raise TypeError("The 'blob' argument must be a bytes object.")
        try:
            # TODO: zlib, gzip or QATZip to accelerate the decompression
            decompressed_data = blob
            frame_msg = frame_pb2.FrameMessage()
            frame_msg.ParseFromString(decompressed_data)

            raw_shape = (frame_msg.raw_height, frame_msg.raw_width, frame_msg.raw_channels)
            raw_frame = np.frombuffer(frame_msg.raw, dtype=np.uint8).reshape(raw_shape)

            frame = Frame(None, frame_msg.pipeline_id, frame_msg.sequence, raw_frame)
            frame.timestamp_new_frame = frame_msg.ts_new
            frame.timestamp_infer_start = frame_msg.ts_infer_start

            return frame
        except Exception as e:
            raise RuntimeError(f"Error during restoring frame from blob: {str(e)}") from e

    @classmethod
    def get_sequence(cls) -> int:
        """Get the monolithic count for the sequence number of a frame.

        The method will return the last sequence number plus one, and update the last sequence
        number to the new value.

        Returns:
            int: The last sequence number.
        """
        if cls.last_sequence > 0x7fffffffffff0000:
            cls.last_sequence = 0
        cls.last_sequence += 1
        return cls.last_sequence

    def normalize(self, target_size: Tuple[int, int]) -> None:
        """Normalize the frame to the target size.

        This method uses OpenCV to resize the frame to the target size.

        Args:
            target_size (Tuple[int, int]): The target size for frame to normalize.

        Raises:
            ValueError: If the target_size is invalid.
        """
        if self._provider.raw_size == target_size:
            return
        if target_size[0] > 0 and target_size[1] > 0:
            self._raw = cv2.resize(self._raw, target_size)
        else:
            raise ValueError(f"Invalid target size: {target_size}")

    def encrypt(self, actor: FrameCipherBase) -> None:
        """Encrypts the frame with a given frame cipher before transferring it outside of TEE.

        The method should be called before transferring the frame outside of TEE.

        Args:
            actor (FrameCipherBase): The frame cipher to use for encryption.
        """
        # TODO: implement the frame encryption

    def decrypt(self, actor: FrameCipherBase) -> None:
        """Decrypts the frame with a given frame cipher after transferring it into TEE.

        The method should be called after transferring the frame into TEE.

        Args:
            actor (FrameCipherBase): The frame cipher to use for decryption.
        """
        # TODO: implement the frame decryption

class QATFrameCipher(FrameCipherBase):
    """Class that uses QAT to accelerate frame encryption and decryption.

    This class implements the `encrypt` and `decrypt` methods from the
    `FrameCipherBase` abstract base class.
    """

    def encrypt(self) -> None:
        """See base class."""
        # TODO: implement the encryption

    def decrypt(self) -> None:
        """See base class."""
        # TODO: implement the decryption
