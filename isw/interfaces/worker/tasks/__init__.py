from ..registry import task_registry
from .handle_test import handle_test
from .handle_update_prompts import handle_update_prompts


def register_tasks():
    task_registry.register(handle_test)
    task_registry.register(handle_update_prompts)
