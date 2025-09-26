from ..interfaces.worker import task_registry
from ..shared.config import set_config
from ..shared.config.celery_adapter import get_worker_config

set_config(get_worker_config())
app = task_registry.get_app()
