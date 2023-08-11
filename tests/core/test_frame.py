"""Tests for the frame module.

This module contains the tests for the frame module.

Functions:
    img: Fixture for raw image.
    filesource: Fixture for Frame.
    frame_instance: Fixture for file source stream provider.
    expected_blob: Fixture for expected blob bytes.
    assert_frame_equal: Assert if two frames are equal.
    test_frame_pipeline_id_setter: Tests the setter of _pipeline_id attribute of Frame class.
    test_frame_pipeline_timestamp_new_frame_setter: Tests the setter of _ts_new attribute of Frame
      class.
    test_frame_pipeline_raw_setter: Tests the setter of _raw attribute of Frame class.
    test_frame_pipeline_timestamp_infer_start_setter: Tests the setter of _ts_infer_start attribute
      of Frame class.
    test_frame_to_blob: Tests the to_blob method of Frame class.
    test_frame_to_blob_failed: Tests the to_blob method of Frame class when serializing fails.
    test_frame_from_blob: Tests the from_blob method of Frame class.
    test_frame_from_blob_invalid_blob: Tests the to_blob method of Frame class with invalid blob.
    test_frame_from_blob_failed: Tests the from_blob method of Frame class when deserializing fails.
    test_frame_get_sequence: Tests the normalize method of Frame class.
    test_frame_normalize_invalid_target_size: Tests the normalize method of Frame class with invalid
      target size.
"""

import os

import cv2
import pytest

from cnap.core import frame, stream
from cnap.core.generated.core.protobuf import frame_pb2

# pylint: disable=no-member
# pylint: disable=redefined-outer-name

CURR_DIR = os.path.dirname(os.path.abspath(__file__))

TRAGET_WIDTH = 300
TRAGET_HEIGHT = 300

TEST_STREAM_NAME = 'classroom'
TEST_PIPELINE_ID = '2bbbdebe-3722-11ee-ba4a-d6bcdc58bce0'
TEST_PIPELINE_ID_SETTER = '2bbbdebe-3722-11ee-ba4a-d6bcdc58bce1'
TEST_FRAME_SEQUENCE = 0x5fffffffffff0000
TEST_FRAME_TIMESTAMP = 0.0
TEST_FRAME_TIMESTAMP_SETTER = 1.1

@pytest.fixture(scope="session")
def img():
    """Fixture for raw image.

    Returns:
        numpy.ndarray: The raw image for test.
    """
    img = cv2.imread(os.path.join(CURR_DIR, "../../docs/cnap_arch.png"))
    return img

@pytest.fixture
def filesource():
    """Fixture for Frame.

    Returns:
        StreamProvider: A `StreamProvider` object instantiated as `FileSource`.
    """
    return stream.FileSource(TEST_STREAM_NAME)

@pytest.fixture
def frame_instance(filesource, img):
    """Fixture for file source stream provider.

    Returns:
        StreamProvider: A `StreamProvider` object instantiated as `FileSource`.
    """
    frame_instance = frame.Frame(filesource, TEST_PIPELINE_ID, TEST_FRAME_SEQUENCE, img)
    frame_instance.timestamp_new_frame = TEST_FRAME_TIMESTAMP
    return frame_instance

@pytest.fixture(scope="session")
def expected_blob(img):
    """Fixture for expected blob bytes.

    Returns:
        bytes: The expected blob bytes for test.
    """
    frame_msg = frame_pb2.FrameMessage()
    frame_msg.pipeline_id = TEST_PIPELINE_ID
    frame_msg.sequence = TEST_FRAME_SEQUENCE
    frame_msg.raw = img.tobytes()
    frame_msg.ts_new = TEST_FRAME_TIMESTAMP
    frame_msg.raw_height = img.shape[0]
    frame_msg.raw_width = img.shape[1]
    frame_msg.raw_channels = 3
    frame_msg.ts_infer_start = 0
    return frame_msg.SerializeToString()

def assert_frame_equal(frame1: frame.Frame, frame2: frame.Frame):
    """Assert if two frames are equal.

    Args:
        frame1 (Frame): The Frame to assert.
        frame2 (Frame): The Frame to assert.
    """
    assert frame1.pipeline_id == frame2.pipeline_id
    assert frame1.sequence == frame2.sequence
    assert (frame1.raw == frame2.raw).all()
    assert frame1.timestamp_new_frame == frame2.timestamp_new_frame
    assert frame1.timestamp_infer_start == frame2.timestamp_infer_start

def test_frame_pipeline_id_setter(frame_instance):
    """Tests the setter of _pipeline_id attribute of Frame class.

    Args:
        frame_instance (Frame): Fixture for Frame.
    """
    frame_instance.pipeline_id = TEST_PIPELINE_ID_SETTER
    assert frame_instance.pipeline_id == TEST_PIPELINE_ID_SETTER

def test_frame_pipeline_timestamp_new_frame_setter(frame_instance):
    """Tests the setter of _ts_new attribute of Frame class.

    Args:
        frame_instance (Frame): Fixture for Frame.
    """
    frame_instance.timestamp_new_frame = TEST_FRAME_TIMESTAMP_SETTER
    assert frame_instance.timestamp_new_frame == TEST_FRAME_TIMESTAMP_SETTER

def test_frame_pipeline_raw_setter(frame_instance):
    """Tests the setter of _raw attribute of Frame class.

    Args:
        frame_instance (Frame): Fixture for Frame.
    """
    raw_setter = cv2.imread(os.path.join(CURR_DIR, "../../docs/cnap_uses.png"))
    frame_instance.raw = raw_setter
    assert frame_instance.raw == raw_setter

def test_frame_pipeline_timestamp_infer_start_setter(frame_instance):
    """Tests the setter of _ts_infer_start attribute of Frame class.

    Args:
        frame_instance (Frame): Fixture for Frame.
    """
    frame_instance.timestamp_infer_start = TEST_FRAME_TIMESTAMP_SETTER
    assert frame_instance.timestamp_infer_start == TEST_FRAME_TIMESTAMP_SETTER

def test_frame_to_blob(frame_instance, expected_blob):
    """Tests the to_blob method of Frame class.

    This test checks if the to_blob method can serialize the frame successfully.

    Args:
        frame_instance (Frame): Fixture for Frame.
        expected_blob (bytes): Fixture for expected blob bytes.
    """
    blob = frame_instance.to_blob()
    assert blob == expected_blob

def test_frame_to_blob_failed(frame_instance):
    """Tests the to_blob method of Frame class when serializing fails.

    Args:
        frame_instance (Frame): Fixture for Frame.
    """
    frame_instance = frame.Frame(filesource, TEST_PIPELINE_ID, 0x5fffffffffff00000000, img)
    with pytest.raises(RuntimeError):
        frame_instance.to_blob()

def test_frame_from_blob(frame_instance, expected_blob):
    """Tests the from_blob method of Frame class.

    This test checks if the from_blob method can deserialize the blob to Frame successfully.

    Args:
        frame_instance (Frame): Fixture for Frame.
        expected_blob (bytes): Fixture for expected blob bytes.
    """
    restored_frame = frame.Frame.from_blob(expected_blob)
    assert_frame_equal(restored_frame, frame_instance)

def test_frame_from_blob_invalid_blob(frame_instance):
    """Tests the to_blob method of Frame class with invalid blob.

    Args:
        frame_instance (Frame): Fixture for Frame.
    """
    with pytest.raises(TypeError):
        frame.Frame.from_blob(frame_instance)

def test_frame_from_blob_failed():
    """Tests the from_blob method of Frame class when deserializing fails."""
    with pytest.raises(RuntimeError):
        frame.Frame.from_blob(b'0000000000000000000')

def test_frame_get_sequence():
    """Tests the get_sequence method of Frame class.

    This test checks if the get_sequence method can increase and reset the sequence correctly.
    """
    assert frame.Frame.get_sequence() == frame.Frame.get_sequence() - 1
    frame.Frame.last_sequence = 0x7fffffffffff0001
    assert frame.Frame.get_sequence() == 1

def test_frame_normalize(frame_instance):
    """Tests the normalize method of Frame class.

    This test checks if the normalize method can normalize the Frame successfully.

    Args:
        frame_instance (Frame): Fixture for Frame.
    """
    frame_instance.normalize((TRAGET_WIDTH, TRAGET_HEIGHT))
    assert frame_instance.raw.shape == (TRAGET_WIDTH, TRAGET_HEIGHT, 3)

def test_frame_normalize_invalid_target_size(frame_instance):
    """Tests the normalize method of Frame class with invalid target size.

    Args:
        frame_instance (Frame): Fixture for Frame.
    """
    with pytest.raises(ValueError):
        frame_instance.normalize((-1, TRAGET_HEIGHT))
    with pytest.raises(ValueError):
        frame_instance.normalize((TRAGET_WIDTH, -1))
