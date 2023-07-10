"""
This module contains the TensorFlowEngine class, which is used to run inference
on a TensorFlow model.
"""
import os
from typing import Tuple

import numpy as np
import tensorflow as tf
import cv2

from core.infereng import InferenceEngine
from core.processors.preprocessor import Preprocessor
from core.processors.postprocessor import Postprocessor, \
    FaceRecognitionPostprocessor, ObjectDetectionPostprocessor

# pylint: disable=no-member

OUTPUT_LAYER_MAPPING = {
    'object-detection': {
        'output_layers': ['detection_boxes', 'detection_scores',
                          'detection_classes', 'num_detections'],
        'drawing': {
            'draw_boxes': True,
            'draw_class_names': True,
        },
    },
    'semantic-segmentation': {
        'output_layers': ['segmentation_output'],
        'drawing': {
            'apply_mask': True,
        },
    },
    'image-classification': {
        'output_layers': ['softmax_tensor'],
        'drawing': {
            'draw_class_name': True,
        },
    },
    'face-recognition': {
        'output_layers': ['facial_landmarks'],
        'drawing': {
            'draw_landmarks': True,
        },
    },
    # Add more mappings for other image processing tasks
}

class TFModelConfig:
    """
    TensorFlow specified configuration for the model.

    Args:
        path (str): Path to the model.
        dtype (str): Data type of the model.
        target (str): Target task of the model.
        device (str, optional): Device to run the model on. Defaults to 'CPU'.
    """
    def __init__(self, path: str, dtype: str, target: str, device: str = 'CPU'):
        self._path = path
        self._dtype = dtype
        self._device = device
        self._target = target

        if self._target in OUTPUT_LAYER_MAPPING:
            task_config = OUTPUT_LAYER_MAPPING[target]
            self._output_layer = task_config['output_layers']
            self._drawing = task_config['drawing']
        else:
            raise ValueError(f"Unsupported inference target: {target}")

    @property
    def path(self) -> str:
        """
        Get the model file path.

        Returns:
            A str object representing the model file path.
        """
        return self._path

    @property
    def dtype(self) -> str:
        """
        Get the data type of the model.

        Returns:
            A str object representing the data type of the model.
        """
        return self._dtype

    @property
    def device(self) -> str:
        """
        Get the device to run the inference on.

        Returns:
            A str object representing the device to run the inference on.
        """
        return self._device

    @property
    def target(self) -> str:
        """
        Get the target of the inference task.

        Returns:
            A str object representing the target of the inference task.
        """
        return self._target

    @property
    def output_layer(self) -> list:
        """
        Get the output layers of the model.

        Returns:
            A list object representing the output layers of the model.
        """
        return self._output_layer

    @property
    def drawing(self) -> dict:
        """
        Get the drawing configuration of the inference task.

        Returns:
            A dict object representing the drawing configuration of the inference task.
        """
        return self._drawing


class TensorFlowPreprocessor(Preprocessor):
    """
    A class for preprocessing input data for TensorFlow models.

    Args:
        input_size (Tuple[int, int]): Expected input size of the model.
        dtype (str): Data type of the model.
    """
    def __init__(self, input_size: Tuple[int, int], dtype: str):
        self._input_size = input_size
        self._dtype = dtype

    def preprocess(self, frame: np.ndarray) -> np.ndarray:
        """
        Preprocess the input frame by resizing and converting to the appropriate data type.

        Args:
            frame: An np.ndarray object representing the input frame.

        Returns:
            An np.ndarray object representing the preprocessed frame.
        """
        if frame.shape[2] != 3:
            raise ValueError("Input frame should have 3 channels (BGR)")

        input_height, input_width = self._input_size

        if input_height is None or input_width is None:
            resized_frame = frame
        else:
            resized_frame = cv2.resize(frame, (input_width, input_height))

        resized_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)
        batch_frame = np.expand_dims(resized_frame, axis=0)

        input_tensor = tf.convert_to_tensor(batch_frame, dtype=tf.as_dtype(self._dtype))

        return input_tensor.numpy()

class TensorFlowPostprocessor(Postprocessor):
    """
    A class for postprocessing output data for TensorFlow models.

    Args:
        target (str): Target task of the model.
        drawing (dict): Settings for drawing the results on the output frame.
    """
    def __init__(self, target: str, drawing: dict):
        self._postprocessor = self._select_postprocessor(target, drawing)

    def _select_postprocessor(self, target: str, drawing: dict) -> Postprocessor:
        """
        Select the appropriate postprocessor for the inference task.

        Args:
            target: A str object representing the target of the inference task.
            drawing: A dict object representing the drawing configuration of the inference task.

        Returns:
            A Postprocessor object representing the appropriate postprocessor for the inference.

        Raises:
            ValueError: If the target is not supported.
            TypeError: If the drawing configuration is not a dict.
        """
        if target == 'object-detection':
            return ObjectDetectionPostprocessor(drawing)
        if target == 'face-recognition':
            return FaceRecognitionPostprocessor(drawing)

        raise ValueError(f"Unsupported inference target: {target}")

    def postprocess(self, frame: np.ndarray, outputs: dict) -> np.ndarray:
        """
        Postprocess the output data by drawing the results on the frame.

        Args:
            frame: An np.ndarray object representing the input frame.
            outputs: A dict object representing the output data.

        Returns:
            An np.ndarray object representing the postprocessed frame.
        """
        return self._postprocessor.postprocess(frame, outputs)

class TensorFlowEngine(InferenceEngine):
    """
    TensorFlow Engine for Inference.

    Args:
        config (TFModelConfig): Configuration of the TensorFlow model.
    """
    def __init__(self, config: TFModelConfig):
        self._model_path = config.path
        self._dtype = config.dtype
        self._target = config.target
        self._drawing = config.drawing
        self._output_layer = config.output_layer
        self._input_size: Tuple[int, int] = None
        self._model = None
        self._session = None

        self._configure_environment()
        self._configure_optimizer()
        self._load_model()

        self._preprocessor = TensorFlowPreprocessor(self._input_size, self._dtype)
        self._postprocessor = TensorFlowPostprocessor(self._target, self._drawing)


    def verify(self) -> bool:
        """
        Verify the TensorFlow Engine object.

        Returns:
            A boolean indicating whether verification was successful.
        """
        return True

    def _load_model(self) -> None:
        """
        Load the TensorFlow model.

        Raises:
            FileNotFoundError: If model file doesn't exist.
            ValueError: If model file extension is not supported.
        """
        if not os.path.exists(self._model_path):
            raise FileNotFoundError(f"Model file not found at {self._model_path}")

        _, ext = os.path.splitext(self._model_path)

        if ext == '.pb':
            self._load_frozen_graph_model()
        elif ext in ['.h5', '.tf', '.hdf5']:  # Explicitly mention all supported extensions.
            self._load_saved_model()
        else:
            raise ValueError(f"Unsupported file extension: {ext}.")

    def preprocess(self, frame: np.ndarray) -> np.ndarray:
        """
        Preprocess the input frame by resizing and converting to the appropriate data type.

        Args:
            frame: An np.ndarray object representing the input frame.

        Returns:
            An np.ndarray object representing the preprocessed frame.
        """
        return self._preprocessor.preprocess(frame)

    def _predict(self, preprocessed_frame: np.ndarray) -> np.ndarray:
        """
        Run inference on the input data.

        Args:
            preprocessed_frame: An np.ndarray object representing the preprocessed input frame.

        Returns:
            An np.ndarray object representing the predicted output.
        """
        if self._session is not None:
            outputs_value = self._session.run(
                self._model['output_tensor'], {self._model['input_tensor']: preprocessed_frame})
        else:
            results = self._model(preprocessed_frame)
            outputs_value = [results[layer].numpy() for layer in self._output_layer]

        outputs = dict(zip(self._output_layer, outputs_value))

        return outputs

    def postprocess(self, frame: np.ndarray, outputs: dict) -> np.ndarray:
        """
        Postprocess the output by drawing boxes and labels on the input frame.

        Args:
            frame: An np.ndarray object representing the input frame.
            outputs: A dictionary object representing the output from the TensorFlow model.

        Returns: An np.ndarray object representing the postprocessed frame.
        """
        return self._postprocessor.postprocess(frame, outputs)

    @property
    def input_size(self) -> Tuple[int, int]:
        """
        Get the input size of the TensorFlow model.

        Returns:
            A tuple object representing the input size.
        """
        return self._input_size

    def _load_frozen_graph_model(self) -> None:
        """
        Load the frozen graph model from the .pb file.

        Raises:
            ValueError: If the input tensor is not found in the graph.
        """
        with tf.io.gfile.GFile(self._model_path, 'rb') as f:
            graph_def = tf.compat.v1.GraphDef()
            graph_def.ParseFromString(f.read())

        graph = tf.Graph()

        # pylint: disable=not-context-manager
        with graph.as_default():
            tf.import_graph_def(graph_def, name='')

            input_tensor = None
            for op in graph.get_operations():
                if op.type == 'Placeholder':
                    input_tensor = op.outputs[0]
                    break
            if input_tensor is None:
                raise ValueError('Failed to find input tensor in the graph.')

            input_height = input_tensor.shape[1] if input_tensor.shape[1] is not None else None
            input_width = input_tensor.shape[2] if input_tensor.shape[2] is not None else None
            self._input_size = (input_height, input_width)

            # Find the output tensor(s) of the graph
            output_tensor = [graph.get_tensor_by_name(layer + ":0") for layer in self._output_layer]

            self._model = {'input_tensor': input_tensor, 'output_tensor': output_tensor}

        self._session = tf.compat.v1.Session(graph=graph)

    def _load_saved_model(self) -> None:
        """
        Load the SavedModel format model.
        """
        loaded_model = tf.saved_model.load(self._model_path)
        serving_default = loaded_model.signatures['serving_default']

        input_tensor_name = list(serving_default.structured_input_signature[1].keys())[0]
        input_tensor = serving_default.inputs[input_tensor_name]
        input_height = input_tensor.shape[1] if input_tensor.shape[1] is not None else None
        input_width = input_tensor.shape[2] if input_tensor.shape[2] is not None else None
        self._input_size = (input_height, input_width)

        self._model = serving_default

    def _configure_optimizer(self) -> None:
        """
        Configure the optimizer.
        """

    def _configure_environment(self) -> None:
        """
        Configure the environment based on the data type.

        Raises:
            ValueError: If data type is not supported.
        """
        if self._dtype == 'float32':
            os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
        elif self._dtype == 'float16':
            os.environ['TF_AUTO_MIXED_PRECISION_GRAPH_REWRITE_ALLOWLIST_ADD'] \
                = 'BiasAdd,Relu6,Mul,AddV2'
            os.environ['TF_AUTO_MIXED_PRECISION_GRAPH_REWRITE_INFERLIST_REMOVE'] \
                = 'BiasAdd,AddV2,Mul'
            os.environ['TF_AUTO_MIXED_PRECISION_GRAPH_REWRITE_CLEARLIST_REMOVE'] \
                = 'Relu6'
        elif self._dtype in ['uint8', 'int8']:
            os.environ['TF_ENABLE_ONEDNN_OPTS'] = '1'
            os.environ['TF_ENABLE_ONEDNN_QUANTIZATION'] = '1'
        else:
            raise ValueError(f"Unsupported data type: {self._dtype}")
