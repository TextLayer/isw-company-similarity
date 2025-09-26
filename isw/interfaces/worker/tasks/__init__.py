from ..registry import task_registry
from .candidate_stage_change import candidate_stage_change
from .handle_test import handle_test
from .handle_update_prompts import handle_update_prompts
from .process_candidate import process_candidate
from .process_technical_submission import process_technical_submission


def register_tasks():
    task_registry.register(handle_test)
    task_registry.register(handle_update_prompts)
    task_registry.register(process_technical_submission)
    task_registry.register(candidate_stage_change)
    task_registry.register(process_candidate)
