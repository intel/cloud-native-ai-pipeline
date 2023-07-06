"""
This module provides an object-oriented design for postprocessing the outputs of
machine learning models. It implements an abstract base class `Postprocessor` and
two concrete postprocessing classes `ObjectDetectionPostprocessor` and
`FaceRecognitionPostprocessor`.

`Postprocessor` serves as a blueprint for custom postprocessing implementations,
while `ObjectDetectionPostprocessor` and `FaceRecognitionPostprocessor` handle
specific postprocessing tasks such as drawing bounding boxes for object detection
and facial landmarks for face recognition, respectively.

These classes can be easily extended or modified to accommodate new postprocessing
strategies and support various machine learning tasks.
"""

from abc import ABC, abstractmethod
from core.processors.category_list import CategoryList
import numpy as np
import cv2

# pylint: disable=no-member

class Postprocessor(ABC):
    """
    Abstract base class for creating custom postprocessing implementations.
    """

    @abstractmethod
    def postprocess(self, frame: np.ndarray, outputs: dict) -> np.ndarray:
        """
        Postprocess the output by applying specific operations on the input frame.

        Args:
            frame: An np.ndarray object representing the input frame.
            outputs: A dictionary object representing the output from the model.

        Returns: An np.ndarray object representing the postprocessed frame.
        """
        raise NotImplementedError("Subclasses should implement the postprocess() method.")

class ObjectDetectionPostprocessor(Postprocessor):
    """
    A class for postprocessing object detection model outputs.
    """

    def __init__(self, drawing: dict):
        if not isinstance(drawing, dict):
            raise TypeError("The 'drawing' argument must be a dictionary.")
        self._drawing = drawing

    def postprocess(self, frame: np.ndarray, outputs: dict) -> np.ndarray:
        """
        Postprocess the output by drawing boxes and labels on the input frame for object detection.

        Args:
        - frame: An np.ndarray object representing the input frame.
        - outputs: A dictionary object representing the output from the TensorFlow model.

        Returns: An np.ndarray object representing the postprocessed frame.
        """
        try:
            if self._drawing.get('draw_boxes'):
                boxes = outputs['detection_boxes']
                labels = outputs['detection_classes']
                for box, label in zip(boxes[0], labels[0]):
                    x1, y1 = int(box[1] * frame.shape[1]), int(box[0] * frame.shape[0])
                    x2, y2 = int(box[3] * frame.shape[1]), int(box[2] * frame.shape[0])
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
                    cv2.putText(frame, CategoryList[label], (x1, y1),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            return frame
        except KeyError as e:
            raise KeyError(f"Missing key in outputs: {str(e)}") from e
        except Exception as e:
            raise RuntimeError(f"Error during postprocessing: {str(e)}") from e

class FaceRecognitionPostprocessor(Postprocessor):
    """
    A class for postprocessing face recognition model outputs.
    """

    def __init__(self, drawing: dict):
        if not isinstance(drawing, dict):
            raise TypeError("The 'drawing' argument must be a dictionary.")
        self._drawing = drawing

    def postprocess(self, frame: np.ndarray, outputs: dict) -> np.ndarray:
        """
        Postprocess the output by drawing facial landmarks on the input frame for face recognition.

        Args:
        - frame: An np.ndarray object representing the input frame.
        - outputs: A dictionary object representing the output from the TensorFlow model.

        Returns: An np.ndarray object representing the postprocessed frame.
        """
        try:
            if self._drawing.get('draw_landmarks'):
                facial_landmarks = outputs['facial_landmarks']
                for landmarks in facial_landmarks:
                    for point in landmarks:
                        x, y = int(point[0]), int(point[1])
                        cv2.circle(frame, (x, y), 2, (0, 255, 0), -1)
            return frame
        except KeyError as e:
            raise KeyError(f"Missing key in outputs: {str(e)}") from e
        except Exception as e:
            raise RuntimeError(f"Error during postprocessing: {str(e)}") from e
