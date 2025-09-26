from ..commands.webooks.validate import ValidateWebhookCommand
from .base import Controller


class WebhooksController(Controller):
    def validate(self, **kwargs):
        return self.executor.execute_write(ValidateWebhookCommand(**kwargs))
