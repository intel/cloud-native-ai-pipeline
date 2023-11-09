"""A Pipeline module.

This module contains the definition of the `Pipeline` class and `PipelineManager` class.

Classes:
    Pipeline: A Class that encapsulates the pipeline information.
    PipelineManager: A class that manage the pipeline with runtime database.
"""

import uuid
import logging
from typing import Dict, Iterator, Any, Tuple

from core.stream import StreamProvider
from core.infereng import InferenceInfo
from core.rtdb import RuntimeDatabaseBase

LOG = logging.getLogger(__name__)

class Pipeline:
    """A Class that encapsulates the pipeline information.

    This class defines the pipeline information, including the pipeline ID, stream provider and
    inference engine information.

    Attributes:
        _id (str): The pipeline ID.
        _provider (StreamProvider): The stream provider of pipeline.
        _infer_engine_dict (dict): The dict of inference engines inforamtion of pipeline.
    """

    def __init__(self, provider: StreamProvider, infer_engine_info: InferenceInfo):
        """Initialize a Pipeline object.

        This constructor initializes a Pipeline object with the given stream provider and
        inference engine information.

        Args:
            provider (StreamProvider): The stream provider of pipeline.
            infer_engine_info (InferenceInfo): The inference engine inforamtion of pipeline.
        """
        self._id = None
        self._provider = provider
        self._infer_engine_dict = {infer_engine_info.id: {'infer_info': dict(infer_engine_info),
                                                         'infer_fps': 0}}

    @property
    def id(self) -> str:
        """str: The pipeline ID (string of UUID)."""
        if self._id is None:
            self._id = uuid.uuid1()
        return str(self._id)

    @id.setter
    def id(self, new_str: str) -> None:
        """Set pipeline ID from string."""
        self._id = uuid.UUID(new_str)

    def __iter__(self) -> Iterator[Tuple[str, Dict[str, Any]]]:
        """The Iterator for Pipeline class."""
        yield 'provider', dict(self._provider)
        yield 'infer_engine_dict', self._infer_engine_dict


class PipelineManager:
    """A class that manage the pipeline with runtime database.

    This class manage the pipeline with runtime database, provides the `register_pipeline`
    and `unregister_pipeline` methods.

    Attributes:
        _db (RuntimeDatabaseBase): The runtime database used by pipeline manager.
    """

    PIPELINE_TABLE = "Pipeline-table"

    def __init__(self, db: RuntimeDatabaseBase):
        """Initialize a PipelineManager object.

        This constructor initializes a PipelineManager object with the given runtime database.

        Args:
            db (RuntimeDatabaseBase): The runtime database used by pipeline manager.
        """
        self._db = db

    def register_pipeline(self, pipeline_obj: Pipeline) -> None:
        """Register a new pipeline.

        Args:
            pipeline_obj (Pipeline): The pipeline object to register.

        Raises:
            ValueError: Propagates the ValueError raised by `save_table_object_dict` if some cases
                are met.
        """
        LOG.debug("Register Pipeline: %s", str(dict(pipeline_obj)))
        try:
            self._db.lock(f"{self.PIPELINE_TABLE}-lock")
            self._db.save_table_object_dict(
                PipelineManager.PIPELINE_TABLE,
                pipeline_obj.id,
                dict(pipeline_obj)
                )
        finally:
            self._db.unlock()

    def unregister_pipeline(self, pipeline_id: str) -> None:
        """Unregister an existing pipeline.

        Args:
            pipeline_id (str): The id of pipeline to unregister.

        Raises:
            ValueError: Propagates the ValueError raised by `del_table_object` if some cases are
                met.
        """
        LOG.debug("Unregister Pipeline: %s", pipeline_id)
        try:
            self._db.lock(f"{self.PIPELINE_TABLE}-lock")
            self._db.del_table_object(PipelineManager.PIPELINE_TABLE, pipeline_id)
        finally:
            self._db.unlock()

    def set_infer_fps(self, pipeline_id: str, infer_info: InferenceInfo, infer_fps: int) -> None:
        """Set inference fps for a pipeline.

        Args:
            pipeline_id (str): The id of pipeline to set inference fps.
            infer_info (InferenceInfo): The inference info to set inference fps.
            infer_fps (int): The inference fps to set.

        Raises:
            ValueError: Propagates the ValueError raised by `get_table_object_dict`
                or `save_table_object_dict` if some cases are met.
        """
        try:
            self._db.lock(f"{self.PIPELINE_TABLE}-lock")
            if self._db.check_table_object_exist(PipelineManager.PIPELINE_TABLE, pipeline_id):
                pipeline_dict = self._db.get_table_object_dict(PipelineManager.PIPELINE_TABLE,
                                                            pipeline_id)
                # Add inference engine to infer_engine_dict if not exist.
                if infer_info.id not in pipeline_dict['infer_engine_dict']:
                    pipeline_dict['infer_engine_dict'][infer_info.id] = \
                                {'infer_info': dict(infer_info),
                                'infer_fps': infer_fps}
                else:
                    pipeline_dict['infer_engine_dict'][infer_info.id]['infer_fps'] = infer_fps
                self._db.save_table_object_dict(
                    PipelineManager.PIPELINE_TABLE,
                    pipeline_id,
                    pipeline_dict
                    )
            else:
                LOG.debug("Pipeline: %s has been unregistered.", pipeline_id)
        finally:
            self._db.unlock()

    def clean_infer_engine(self, infer_info_id: str) -> None:
        """Clean inference engine in infer_engine_dict.

        Args:
            infer_info_id (str): The id of inference info to clear inference fps.

        Raises:
            ValueError: Propagates the ValueError raised by `get_all_table_objects_dict`
                or `save_table_object_dict` if some cases are met.
        """
        try:
            self._db.lock(f"{self.PIPELINE_TABLE}-lock")
            pipeline_dicts = self._db.get_all_table_objects_dict(PipelineManager.PIPELINE_TABLE)
            for pipeline_id, pipeline_dict in pipeline_dicts.items():
                if infer_info_id in pipeline_dict['infer_engine_dict']:
                    del pipeline_dict['infer_engine_dict'][infer_info_id]
                    if self._db.check_table_object_exist(PipelineManager.PIPELINE_TABLE,
                                                         pipeline_id):
                        self._db.save_table_object_dict(
                            PipelineManager.PIPELINE_TABLE,
                            pipeline_id,
                            pipeline_dict
                            )
                    else:
                        LOG.debug("Pipeline: %s has been unregistered.", pipeline_id)
        finally:
            self._db.unlock()
