import inspect
from typing import Any, Callable, ClassVar, get_type_hints

from celery import Celery
from celery.result import AsyncResult
from kombu import Exchange, Queue

from ...core.errors import ValidationException
from ...core.utils.helpers import is_dict_like
from ...shared.config.celery_adapter import get_worker_config
from ...shared.logging.logger import logger


class TaskRegistry:
    _app: Celery
    _dlx_queue = "worker_dlx_queue"
    _queue = "worker_queue"
    _queue_retries = 3
    _queue_retry_interval_start = 20
    _queue_retry_interval_step = 2
    _tasks: ClassVar[dict] = {}

    def __init__(self):
        """
        Initialize the TaskRegistry.

        This will configure the Celery app and register the tasks.
        In production, the queues are configured to be durable and persistent,
        with a dead letter exchange and retry mechanism.

        Args:
            None

        Returns:
            None
        """

        conf = get_worker_config()
        app = Celery(
            "app_worker",
            broker_url=conf.celery_broker_url,
            result_backend=conf.celery_result_backend,
            task_always_eager=conf.celery_task_always_eager,
            task_ignore_result=conf.celery_task_ignore_result,
        )

        try:
            if not conf.celery_task_always_eager:
                app.conf.task_queues = (
                    Queue(
                        self._queue,
                        exchange=Exchange(self._queue, type="direct"),
                        routing_key=self._queue,
                        queue_arguments={
                            "x-dead-letter-exchange": self._dlx_queue,
                            "x-dead-letter-routing-key": self._dlx_queue,
                        },
                        durable=True,
                    ),
                    Queue(
                        self._dlx_queue,
                        exchange=Exchange(self._dlx_queue, type="direct"),
                        routing_key=self._dlx_queue,
                        queue_arguments={},
                        durable=True,
                    ),
                )

                app.conf.task_default_queue = self._queue
                app.conf.task_default_exchange = self._queue
                app.conf.task_default_routing_key = self._queue
                app.conf.task_default_retry_delay = self._queue_retry_interval_start
                app.conf.task_max_retries = self._queue_retries
                app.conf.task_acks_late = True
                app.conf.task_reject_on_worker_lost = True
        except Exception as e:
            logger.error(f"Error configuring Celery: {e}")
        finally:
            self._app = app

    def conduct_health_check(self) -> str:
        """
        Conduct a health check on the worker by deferring a test task
        and asserting that the result is not None.

        Args:
            None

        Returns:
            A string indicating the health of the worker.
        """
        try:
            if not self.defer(
                "handle_test",
                {
                    "message": "Are we healthy?",
                },
            ):
                raise Exception("Health check failed")

            return "online"
        except Exception as e:
            logger.warning(f"Health check incomplete: {e}")
            return "offline"

    def create_task(self, name: str, fn: Callable) -> Callable:
        """
        Create a task using Celery's decorator to bind and retry the function automatically.

        Args:
            name: The name of the task.
            fn: The function to create a task from.

        Returns:
            A Celery task.
        """

        @self._app.task(acks_late=True, bind=True, max_retries=self._queue_retries, name=name)
        def task(celery_self, *args, **kwargs) -> Any:
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                raise celery_self.retry(exc=e, countdown=self._queue_retry_interval_start) from e

        return task

    def defer(self, task_name: str, data: dict = None) -> AsyncResult:
        """
        Defer a task to be executed by the worker.

        Args:
            task_name: The name of the task to defer.
            data: The data to pass to the task.

        Returns:
            An AsyncResult object.
        """
        task = self._tasks.get(task_name)

        if not task:
            raise ValidationException(f"Task unknown to the registry: {task_name}")

        return task.apply_async(args=(data or {},), queue=self._queue)

    def get_app(self) -> Celery:
        """
        Get the Celery app.

        Args:
            None

        Returns:
            The Celery app.
        """
        return self._app

    def register(self, fn):
        """
        Register a task with the registry.
        It will validate the task to ensure it accepts a single dict parameter.

        Args:
            fn: The function to register.

        Returns:
            None
        """
        task_name = fn.__name__

        try:
            params = list(inspect.signature(fn).parameters.values())

            if len(params) != 1:
                raise ValidationException(f"Task {task_name} must accept exactly one parameter")

            if not is_dict_like(get_type_hints(fn).get("data")):
                raise ValidationException(f"Task {task_name} must accept a single dict parameter")

            self._tasks[task_name] = self.create_task(task_name, fn)
        except Exception as e:
            logger.error(f"Error registering task {task_name}: {e}")
            raise e


task_registry = TaskRegistry()
