"""A Metrics module.

This module provides a class to manage metrics in a Prometheus-based application.
It provides methods to create, track, and update metrics.

Classes:
    MetricType: An enum for the type of metric.
    ErrorMessage: An enum for error messages.
    MetricsManager: A class to manage metrics in a Prometheus-based application.
"""

from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, Union
from threading import Lock
from prometheus_client import Counter, Gauge, Histogram, Summary

class MetricType(Enum):
    """An enum for the type of metric.

    This enum defines the types of metrics that can be created.
    """
    COUNTER = 'Counter'
    GAUGE = 'Gauge'
    HISTOGRAM = 'Histogram'
    SUMMARY = 'Summary'


class ErrorMessage(Enum):
    """An enum for error messages.

    This enum defines the error messages that can be raised.
    """
    METRIC_EXISTS = 'Metric {} already exists'
    INVALID_METRIC_TYPE = 'Invalid metric type: {}'
    METRIC_DOES_NOT_EXIST = 'Metric {} does not exist'
    METRIC_TYPE_MISMATCH = 'Metric {} is not a {}'


class MetricsManager:
    """A class to manage metrics in a Prometheus-based application.

    This class provides methods to create, track, and update metrics.

    Attributes:
        metrics (dict): A dictionary of all metrics.
    """

    _instance = None
    _lock = Lock()

    def __new__(cls, *args, **kwargs):
        """Creates a singleton instance of the MetricsManager.

        This method creates a singleton instance of the MetricsManager.

        Returns:
            MetricsManager: The singleton instance of the MetricsManager.
        """
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance

    _METRIC_TYPE_MAP = {
        MetricType.COUNTER: Counter,
        MetricType.GAUGE: Gauge,
        MetricType.HISTOGRAM: Histogram,
        MetricType.SUMMARY: Summary,
    }

    def __init__(self):
        """Initializes the MetricsManager with an empty metrics dictionary.

        This method initializes the MetricsManager with an empty metrics dictionary.
        """
        if not hasattr(self, 'metrics'):
            self.metrics: Dict[str, Union[Counter, Gauge, Histogram, Summary]] = {}

    def get_metric(self, metric_name: str, metric_type: MetricType) -> Union[
        Counter, Gauge, Histogram, Summary]:
        """Returns the metric with the specified name and type.

        Args:
            metric_name (str): The name of the metric.
            metric_type (type): The type of the metric.

        Returns:
            Union[Counter, Gauge, Histogram, Summary]: The metric with the specified name and type.

        Raises:
            ValueError: If the specified metric does not exist or the metric type is invalid.
        """
        with self._lock:
            metric = self.metrics.get(metric_name)
            if metric is None:
                raise ValueError(ErrorMessage.METRIC_DOES_NOT_EXIST.value.format(metric_name))

            metric_class = self._METRIC_TYPE_MAP.get(metric_type)
            if metric_class is None:
                raise ValueError(ErrorMessage.INVALID_METRIC_TYPE.value.format(metric_type))

            if not isinstance(metric, metric_class):
                raise ValueError(ErrorMessage.METRIC_TYPE_MISMATCH.value.format(
                    metric_name, metric_class.__name__))

            return metric

    def create_metric(self, metric_type: MetricType, metric_name: str, description: str) -> None:
        """Creates a new metric.

        This method will create a new metric of the specified type and stores it in the
        metrics dictionary.

        Args:
            metric_type (MetricType): The type of the metric.
            metric_name (str): The name of the metric. Must be unique across all metrics.
            description (str): The description of the metric.

        Raises:
            ValueError: If the specified metric already exists or the metric type is invalid.
        """
        with self._lock:
            if metric_name in self.metrics:
                raise ValueError(f'Metric {metric_name} already exists')

            metric_class = self._METRIC_TYPE_MAP.get(metric_type)
            if metric_class is None:
                raise ValueError(f'Invalid metric type: {metric_type}')

            self.metrics[metric_name] = metric_class(metric_name, description)

    def latency_decorator(self,
                          metric_name: str) -> Callable[..., Callable[..., Any]]:
        """Returns a decorator that tracks the latency of the decorated function.

        Args:
            metric_name (str): The name of the Histogram metric to track the latency.

        Returns:
            Callable[..., Callable[..., Any]]: A decorator that tracks the latency of the decorated
                function.

        Raises:
            ValueError: If the specified metric does not exist or is not a Histogram.
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                metric = self.get_metric(metric_name, MetricType.HISTOGRAM)
                with metric.time():
                    return func(*args, **kwargs)
            return wrapper
        return decorator

    def increment_counter(self, metric_name: str, by: float = 1.0) -> None:
        """Increments a Counter metric by the specified amount.

        Args:
            metric_name (str): The name of the Counter metric to increment.
            by (int, optional): The amount to increment by. Default is 1.

        Raises:
            ValueError: If the specified metric does not exist or is not a Counter.
        """
        metric = self.get_metric(metric_name, MetricType.COUNTER)
        metric.inc(by)

    def set_gauge(self, metric_name: str, value: float) -> None:
        """Sets a Gauge metric to the specified value.

        Args:
            metric_name (str): The name of the Gauge metric to set.
            value (float): The value to set the Gauge to.

        Raises:
            ValueError: If the specified metric does not exist or is not a Gauge.
        """
        metric = self.get_metric(metric_name, MetricType.GAUGE)
        metric.set(value)

    def observe_summary(self, metric_name: str, value: float) -> None:
        """Observes a value in a Summary metric.

        Args:
            metric_name (str): The name of the Summary metric to observe a value in.
            value (float): The value to observe.

        Raises:
            ValueError: If the specified metric does not exist or is not a Summary.
        """
        metric = self.get_metric(metric_name, MetricType.SUMMARY)
        metric.observe(value)

    def observe_histogram(self, metric_name: str, value: float) -> None:
        """Observes a value in a Histogram metric.

        Args:
            metric_name (str): The name of the Histogram metric to observe a value in.
            value (float): The value to observe.

        Raises:
            ValueError: If the specified metric does not exist or is not a Histogram.
        """
        metric = self.get_metric(metric_name, MetricType.HISTOGRAM)
        metric.observe(value)

    def get_metrics(self) -> Dict[str, Union[Counter, Gauge, Histogram, Summary]]:
        """Returns the dictionary of all metrics.

        Returns:
            dict: The dictionary of all metrics.
        """
        with self._lock:
            return self.metrics.copy()
