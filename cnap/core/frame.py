"""
This module contains the definition of frame class, which encapsulates raw frame
and related information for transferring data between micro services, it can be
simply encoded and decoded by protobuf. A frame should include enough information
for traceability, observability, etc.

In addition, this module provides an object-oriented design for frame cipher to
encrypt and decrypt frame. The abstract base class `FrameCipherBase` serves as a
blueprint for custom frame cipher implementations while `QATFrameCipher` provides
an implementation to encrypt and decrypt frame accelerated with QAT, it is TODO now.
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
    """
    Abstract base class frame cipher implementations.
    """

    @abstractmethod
    def encrypt(self) -> None:
        """
        Encrypt the frame

        Return: None
        """
        raise NotImplementedError("Subclasses should implement encrypt() method.")

    @abstractmethod
    def decrypt(self) -> None:
        """
        Decrypt the frame

        Return: None
        """
        raise NotImplementedError("Subclasses should implement decrypt method.")

class Frame:
    """
    A class that encapsulates raw frame and related information, can be simply
    encoded and decoded by protobuf.
    """

    # Class variable to calculate the last sequence number
    last_sequence = 0

    def __init__(self, provider: StreamProvider, pipeline_id: str,
                 sequence: int, raw_frame: np.ndarray):
        """
        Initialize a Frame object.

        Args:
            provider: The stream provider of the frame.
            pipeline_id: The pipeline id of the frame.
            sequenece: The initial sequenece number of the frame.
            raw_frame: The raw frame of the frame.
        """
        self._provider = provider
        self._pipeline_id = pipeline_id
        self._sequence = sequence
        self._raw = raw_frame
        self._ts_new = time.time()
        self._ts_infer_start = 0

    @property
    def pipeline_id(self) -> str:
        """
        Get the pipeline ID.
        """
        return self._pipeline_id

    @pipeline_id.setter
    def pipeline_id(self, new_str: str) -> None:
        """
        Set pipeline ID from string
        """
        self._pipeline_id = new_str

    @property
    def sequence(self) -> int:
        """
        Get the monolithic counter for the frame sequence number.
        """
        return self._sequence

    @property
    def timestamp_new_frame(self) -> float:
        """
        Get the timestamp of the beginning of this new frame.
        """
        return self._ts_new

    @timestamp_new_frame.setter
    def timestamp_new_frame(self, timestamp: float) -> None:
        """
        Set the timestamp of the beginning of this new frame.
        """
        self._ts_new = timestamp

    @property
    def raw(self) -> np.ndarray:
        """
        Get the raw frame.
        """
        return self._raw

    @raw.setter
    def raw(self, raw_frame: np.ndarray) -> None:
        """
        Set raw frame.
        """
        self._raw = raw_frame

    @property
    def timestamp_infer_start(self) -> float:
        """
        Get the timestamp of the inference's start point.
        """
        return self._ts_infer_start

    @timestamp_infer_start.setter
    def timestamp_infer_start(self, timestamp: float) -> None:
        """
        Set the timestamp of the inference's start point.
        """
        self._ts_infer_start = timestamp

    def to_blob(self) -> bytes:
        """
        Encode the raw frame to a blob for transferring to the infer queue.

        Returns:
            bytes: the blob encoded from raw frame.

        Raises:
            RuntimeError: if any errors while encoding.
        """
        try:
            # Get the frame shape info
            if len(self._raw.shape) == 3:
                height, width, channel = self._raw.shape
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
        """
        Restore a frame instance from a blob.

        Returns:
            Frame: the frame restored from a blob.

        Raises:
            TypeError: if the type of 'blob' argument is not bytes type.
            RuntimeError: if any errors while decoding.
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
        """
        Monolithic count for the sequence number of a frame.

        Returns:
            int: the last sequence number.
        """
        if cls.last_sequence > 0x7fffffffffff0000:
            cls.last_sequence = 0
        cls.last_sequence += 1
        return cls.last_sequence

    def normalize(self, target_size: Tuple[int, int]) -> None:
        """
        Normalize the frame to the target size.

        Args:
            target_size: the target size for frame to normalize

        Returns: None

        Raises:
            ValueError: if the target_size is invalid.
        """
        if self._provider.raw_size == target_size:
            return
        if target_size[0] > 0 and target_size[1] > 0:
            self._raw = cv2.resize(self._raw, target_size)
        else:
            raise ValueError(f"Invalid target size: {target_size}")

    def encrypt(self, actor: FrameCipherBase) -> None:
        """
        Encrypt the frame before transferring it outside of TEE.
        """
        # TODO: implement the frame encryption

    def decrypt(self, actor: FrameCipherBase) -> None:
        """
        Decrypt the frame after transferring it into TEE.
        """
        # TODO: implement the frame decryption

class QATFrameCipher(FrameCipherBase):
    """
    Use QAT to accelerate frame encryption and decryption.
    """

    def encrypt(self) -> None:
        # TODO: implement the encryption
        pass

    def decrypt(self) -> None:
        # TODO: implement the decryption
        pass
