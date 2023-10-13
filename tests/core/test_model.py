"""Tests for the model module.

This module contains the tests for the model module.

Functions:
    test_model_metrics_accuracy_property: Tests the property of _accuracy attribute of ModelMetrics
      class.
    test_model_metrics_precision_property: Tests the property of _precision attribute of
      ModelMetrics class.
    test_model_metrics_recall_property: Tests the property of _recall attribute of ModelMetrics
      class.
    test_model_metrics_f1_score_property: Tests the property of _f1_score attribute of ModelMetrics
      class.
    test_model_metrics_loss_property: Tests the property of _loss attribute of ModelMetrics class.
    test_model_details_name_property: Tests the property of _name attribute of ModelDetails class.
    test_model_details_version_property: Tests the property of _version attribute of ModelDetails
      class.
    test_model_details_framework_property: Tests the property of _framework attribute of
      ModelDetails class.
    test_model_details_target_property: Tests the property of _target attribute of ModelDetails
      class.
    test_model_details_dtype_property: Tests the property of _dtype attribute of ModelDetails class.
    test_model_info_id_property: Tests the property of _id attribute of ModelInfo class.
    test_model_info_path_property: Tests the property of _path attribute of ModelInfo class.
    test_model_info_details_property: Tests the property of _details attribute of ModelInfo class.
    test_model_info_uploaded_date_property: Tests the property of _uploaded_date attribute of
      ModelInfo class.
    test_model_info_metrics_property: Tests the property of _metrics attribute of ModelInfo class.
    test_model_init_valid_model_provider: Tests the __init__ method of Model class with invalid
      model provider.
    test_model_model_info_property: Tests the property of _model_info attribute of Model class.
    test_model_model_binary_property: Tests the property of _model_binary attribute of Model class.
    test_model_iter: Tests the Iterator of Model class.
"""

import pytest

from cnap.core import model
from tests.core.conftest import TEST_MODEL_ID, TEST_FRAMEWORK, TEST_TARGET, TEST_MODEL_NAME, \
    TEST_MODEL_VERSION, TEST_MODEL_PATH

def test_model_metrics_accuracy_property(model_metrics):
    """Tests the property of _accuracy attribute of ModelMetrics class.

    Args:
        model_metrics (ModelMetrics): Fixture for ModelMetrics.
    """
    assert model_metrics.accuracy == 0

def test_model_metrics_precision_property(model_metrics):
    """Tests the property of _precision attribute of ModelMetrics class.

    Args:
        model_metrics (ModelMetrics): Fixture for ModelMetrics.
    """
    assert model_metrics.precision == 0

def test_model_metrics_recall_property(model_metrics):
    """Tests the property of _recall attribute of ModelMetrics class.

    Args:
        model_metrics (ModelMetrics): Fixture for ModelMetrics.
    """
    assert model_metrics.recall == 0

def test_model_metrics_f1_score_property(model_metrics):
    """Tests the property of _f1_score attribute of ModelMetrics class.

    Args:
        model_metrics (ModelMetrics): Fixture for ModelMetrics.
    """
    assert model_metrics.f1_score == 0

def test_model_metrics_loss_property(model_metrics):
    """Tests the property of _loss attribute of ModelMetrics class.

    Args:
        model_metrics (ModelMetrics): Fixture for ModelMetrics.
    """
    assert model_metrics.loss == 0

def test_model_details_name_property(model_details):
    """Tests the property of _name attribute of ModelDetails class.

    Args:
        model_details (ModelDetails): Fixture for ModelDetails.
    """
    assert model_details.name == TEST_MODEL_NAME

def test_model_details_version_property(model_details):
    """Tests the property of _version attribute of ModelDetails class.

    Args:
        model_details (ModelDetails): Fixture for ModelDetails.
    """
    assert model_details.version == TEST_MODEL_VERSION

def test_model_details_framework_property(model_details):
    """Tests the property of _framework attribute of ModelDetails class.

    Args:
        model_details (ModelDetails): Fixture for ModelDetails.
    """
    assert model_details.framework == TEST_FRAMEWORK

def test_model_details_target_property(model_details):
    """Tests the property of _target attribute of ModelDetails class.

    Args:
        model_details (ModelDetails): Fixture for ModelDetails.
    """
    assert model_details.target == TEST_TARGET

def test_model_details_dtype_property(model_details):
    """Tests the property of _dtype attribute of ModelDetails class.

    Args:
        model_details (ModelDetails): Fixture for ModelDetails.
    """
    assert model_details.dtype == 'int8'

def test_model_info_id_property(model_info):
    """Tests the property of _id attribute of ModelInfo class.

    Args:
        model_info (ModelInfo): Fixture for ModelInfo.
    """
    assert model_info.id == TEST_MODEL_ID

def test_model_info_path_property(model_info):
    """Tests the property of _path attribute of ModelInfo class.

    Args:
        model_info (ModelInfo): Fixture for ModelInfo.
    """
    assert model_info.path == TEST_MODEL_PATH

def test_model_info_details_property(model_info, model_details):
    """Tests the property of _details attribute of ModelInfo class.

    Args:
        model_info (ModelInfo): Fixture for ModelInfo.
        model_details (ModelDetails): Fixture for ModelDetails.
    """
    assert dict(model_info.details) == dict(model_details)

def test_model_info_uploaded_date_property(model_info):
    """Tests the property of _uploaded_date attribute of ModelInfo class.

    Args:
        model_info (ModelInfo): Fixture for ModelInfo.
    """
    assert model_info.uploaded_date == 0

def test_model_info_metrics_property(model_info, model_metrics):
    """Tests the property of _metrics attribute of ModelInfo class.

    Args:
        model_info (ModelInfo): Fixture for ModelInfo.
        model_details (ModelDetails): Fixture for ModelDetails.
    """
    assert dict(model_info.metrics) == dict(model_metrics)

def test_model_init_valid_model_provider(httpserver):
    """Tests the __init__ method of Model class with invalid model provider.

    Args:
        httpserver (HTTPServer): Fixture which starts http server.
    """
    model_provider = "invalid_provider"
    model_info_url = httpserver.url_for("/models")
    with pytest.raises(RuntimeError):
        model.Model(model_provider, model_info_url, TEST_MODEL_ID)

def test_model_model_info_property(model_info, model_instance):
    """Tests the property of _model_info attribute of Model class.

    Args:
        model_info (ModelInfo): Fixture for ModelInfo.
        model_instance (Model): Fixture for Model.
    """
    assert dict(model_instance.model_info) == dict(model_info)

def test_model_model_binary_property(model_data, model_instance):
    """Tests the property of _model_binary attribute of Model class.

    Args:
        model_data (bytes): Fixture for ModelInfo.
        model_instance (Model): Fixture for Model.
    """
    assert model_instance.model_binary == model_data

def test_model_iter(model_info, model_data, model_instance):
    """Tests the Iterator of Model class.

    Args:
        model_info (ModelInfo): Fixture for ModelInfo.
        model_data (bytes): Fixture for ModelInfo.
        model_instance (Model): Fixture for Model.
    """
    assert dict(model_instance) == {"model_info": dict(model_info),
                                    "model_binary": model_data}
