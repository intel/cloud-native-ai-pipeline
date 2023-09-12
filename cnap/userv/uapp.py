"""A Uapp module.

Application template for Micro Service apps and tasks classes.

Classes:
    MicroServiceTask: A base class for micro service task of threading based Task.
    MicroAppBase: An abstract base class for micro service app.
"""

import os
import sys
import logging
import asyncio
import threading
from abc import ABC, abstractmethod
from typing import Callable, Any, Optional

LOG = logging.getLogger(__name__)

class MicroServiceTask(threading.Thread):
    """A base class for micro service task of threading based Task.

    In general, a cloud native app may consists several threading tasks.

    Attributes:
        _is_asyncio (bool): A boolean variable that flags if the task is asyncio or not.
        _exec_func (Callable): The execute function of the micro service task.
        _event_loop (asyncio.AbstractEventLoop): The event loop of the asyncio tasks.
        _is_task_stopping (bool): A boolean variable that flags if the task is stopping or not.
        _name (str): The name of the micro service task.
    """

    _task_list = []

    def __init__(self, name: str=None, exec_func: Callable=None, is_asyncio: bool=False):
        """Initialize a MicroServiceTask object.

        Args:
            name (str): The name of the micro service task.
            exec_func (Callable): The execute function of the micro service task.
            is_asyncio (bool): A boolean variable that flags if the task is asyncio or not.
        """
        threading.Thread.__init__(self)
        self._is_asyncio = is_asyncio
        self._exec_func = exec_func
        self._event_loop = None
        self._is_task_stopping = False
        self._name = name
        if self not in MicroServiceTask._task_list:
            MicroServiceTask._task_list.append(self)

    @property
    def name(self):
        """The name of the micro service task."""
        if self._name is None:
            self._name = self.__class__.__name__
        return self._name

    @classmethod
    def stop_all_tasks(cls):
        """Stops all tasks."""
        for task in MicroServiceTask._task_list:
            if task.is_alive():
                task.stop()

    @classmethod
    def wait_all_tasks_end(cls):
        """Wait all task end."""
        for task in MicroServiceTask._task_list:
            if task.is_alive():
                task.join()
        LOG.info("All task stopped! Bye~~~")

    def run(self):
        """Main entry for a task."""
        if self._is_asyncio:
            self._event_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._event_loop)

        LOG.info("[Task-%s] starting!", self.name)
        try:
            if self._exec_func is not None:
                # pass task object to callback function
                self._exec_func(self)
            else:
                self.execute()
        except:
            LOG.error("[Task-%s] Failed!", self.name, exc_info=True)
            MicroServiceTask.stop_all_tasks()
            sys.exit(1)
        LOG.info("[Task - %s] Completed!", self.name)

    def execute(self):
        """The task logic of micro service task.

        Inherited class should implement customized task logic.

        Raises:
            NotImplementedError: If the subclasses don't implement the method.
        """
        raise NotImplementedError("inherited class must implement execute() method.")

    @property
    def is_task_stopping(self):
        """A boolean variable that flags if the task is stopping or not."""
        return self._is_task_stopping

    def stop(self):
        """Stop a running task."""
        LOG.info("Stopping Task - %s", self.name)
        if self._is_asyncio:
            try:
                self._event_loop.stop()
            except:
                LOG.error("Fail to stop event loop", exc_info=True)
        self._is_task_stopping = True

class MicroAppBase(ABC):
    """An abstract base class for micro service app.

    A cloud native application should accept the parameters from environment
    variable. There might be one or more tasks. Accept the interrupt for
    kubernetes lifecycle management, etc.
    """

    def __init__(self):
        """Initialize a MicroAppBase object."""
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)-15s %(levelname)-6s [%(module)-6s] %(message)s')
        self.init()

    @abstractmethod
    def init(self):
        """Initialization entry for an application instance.

        Raises:
            NotImplementedError: If the subclasses don't implement the method.
        """
        raise NotImplementedError("Subclasses should implement init() method.")

    @staticmethod
    def get_env(key, default: Optional[Any]=None) -> Optional[Any]:
        """Get environment variable.

        Args:
            key (str): The name of the environment variable.
            default (Optional[Any]): The default value to return if the environment variable
                does not exist.

        Returns:
            Optional[Any]: The value of the environment variable or the default value.
        """
        if key not in os.environ:
            LOG.warning("Cloud not find the key %s in environment, use "
                        "default value %s", key, str(default))
            return default
        return os.environ[key]

    def run_and_wait_task(self):
        """Run and wait all tasks."""
        try:
            if not self.run():
                MicroServiceTask.stop_all_tasks()
                MicroServiceTask.wait_all_tasks_end()
                sys.exit(1)
        except:
            LOG.error("Fail to run.", exc_info=True)
            self.stop()
            sys.exit(1)
        MicroServiceTask.wait_all_tasks_end()
        self.cleanup()

    @abstractmethod
    def run(self):
        """Application main logic provided by inherited class.

        Raises:
            NotImplementedError: If the subclasses don't implement the method.
        """
        raise NotImplementedError("Subclasses should implement run() method.")

    @abstractmethod
    def cleanup(self):
        """Cleanup.

        Raises:
            NotImplementedError: If the subclasses don't implement the method.
        """
        raise NotImplementedError("Subclasses should implement cleanup() method.")

    def stop(self):
        """Stop an application instance."""
        MicroServiceTask.stop_all_tasks()
        MicroServiceTask.wait_all_tasks_end()
        self.cleanup()
