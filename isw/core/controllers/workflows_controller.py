from ..commands.workflows.run_evals import RunEvalsWorkflowCommand
from ..commands.workflows.sync_prompts import SyncPromptsCommand
from ..commands.workflows.update_prompts import UpdatePromptsCommand
from .base import Controller


class WorkflowsController(Controller):
    def run_evals(self, **kwargs):
        return self.executor.execute_write(RunEvalsWorkflowCommand(**kwargs))

    def sync_prompts(self, **kwargs):
        return self.executor.execute_write(SyncPromptsCommand(**kwargs))

    def update_prompts(self, **kwargs):
        return self.executor.execute_write(UpdatePromptsCommand(**kwargs))
