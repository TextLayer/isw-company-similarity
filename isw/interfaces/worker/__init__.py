from isw.interfaces.worker.registry import task_registry
from isw.interfaces.worker.tasks import register_tasks

register_tasks()

__all__ = ["task_registry"]
