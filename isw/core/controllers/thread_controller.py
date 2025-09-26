from ..commands.threads.get_models import GetModelsCommand
from ..commands.threads.process_chat_message import ProcessChatMessageCommand
from .base import Controller


class ThreadController(Controller):
    def get_models(self, **kwargs):
        return self.executor.execute_read(GetModelsCommand(**kwargs))

    def process_chat_message(self, **kwargs):
        return self.executor.execute_write(ProcessChatMessageCommand(**kwargs))
