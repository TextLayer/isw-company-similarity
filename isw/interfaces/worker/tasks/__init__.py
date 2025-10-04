from ..registry import task_registry
from .handle_test import handle_test


def register_tasks():
    task_registry.register(handle_test)
