"""A Postprocessor module.

This module provides an object-oriented design for postprocessing the outputs of
machine learning models.

Classes:
    Postprocessor: An abstract base class for creating custom postprocessing implementations.
    ObjectDetectionPostprocessor: A concrete class implementing the Postprocessor for object
      detection model outputs.
    FaceRecognitionPostprocessor: A concrete class implementing the Postprocessor for face
      recognition model outputs.
"""

from abc import ABC, abstractmethod
from core.processors.category_list import CategoryList
import numpy as np
import cv2

# pylint: disable=no-member

class Postprocessor(ABC):
    """An abstract base class for creating custom postprocessing implementations.

    This class serves as a blueprint for subclasses that need to implement
    `postprocess` method for different types of postprocessing tasks.
    """

    @abstractmethod
    def postprocess(self, frame: np.ndarray, outputs: dict) -> np.ndarray:
        """Postprocess the output by applying specific operations on the input frame.

        Args:
            frame (np.ndarray): An np.ndarray object representing the input frame.
            outputs (dict): A dictionary object representing the output from the model.

        Returns:
            np.ndarray: An np.ndarray object representing the postprocessed frame.

        Raises:
            NotImplementedError: If the subclasses don't implement the method.
            KeyError: If missing key in outputs.
            RuntimeError: If any errors during postprocessing.
        """
        raise NotImplementedError("Subclasses should implement the postprocess() method.")

class ObjectDetectionPostprocessor(Postprocessor):
    """A concrete class implementing the Postprocessor for object detection model outputs.

    This class implement `postprocess` method defined in `Postprocessor` abstract base class
    for object detection model outputs.

    Attributes:
        _drawing (dict): A dict object representing the drawing configuration.
    """

    def __init__(self, drawing: dict):
        """Initialize a ObjectDetectionPostprocessor object.

        Args:
            drawing (dict): A dict object representing the drawing configuration.

        Raises:
            TypeError: If the drawing argument is not a dictionary.
        """
        if not isinstance(drawing, dict):
            raise TypeError("The 'drawing' argument must be a dictionary.")
        self._drawing = drawing

    def postprocess(self, frame: np.ndarray, outputs: dict) -> np.ndarray:
        """Implement the postprocess method for object detection model outputs.

        The method overrides the `postprocess` method defined in `Postprocessor`
        abstract base class.
        Postprocess the output by drawing boxes and labels on the input frame for
        object detection.
        """
        frame = frame.copy()
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
    """A concrete class implementing the Postprocessor for face recognition model outputs.

    This class implement `postprocess` method defined in `Postprocessor` abstract base class
    for face recognition model outputs.

    Attributes:
        _drawing (dict): A dict object representing the drawing configuration.
    """

    def __init__(self, drawing: dict):
        """Initialize a FaceRecognitionPostprocessor object.

        Args:
            drawing (dict): A dict object representing the drawing configuration.

        Raises:
            TypeError: If the drawing argument is not a dictionary.
        """
        if not isinstance(drawing, dict):
            raise TypeError("The 'drawing' argument must be a dictionary.")
        self._drawing = drawing

    def postprocess(self, frame: np.ndarray, outputs: dict) -> np.ndarray:
        """Implement the postprocess method for face recognition model outputs.

        The method overrides the `postprocess` method defined in `Postprocessor`
        abstract base class.
        Postprocess the output by drawing boxes and labels on the input frame for
        object detection.
        """
        frame = frame.copy()
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
