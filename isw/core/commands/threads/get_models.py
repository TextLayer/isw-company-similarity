from typing import Any, Dict, List

from ...services.llm import ChatClient
from ..base import ReadCommand


class GetModelsCommand(ReadCommand):
    def __init__(self):
        pass

    def execute(self) -> Dict[str, List[Dict[str, Any]]]:
        client = ChatClient()

        return {
            "chat_models": client.get_models(model_type="chat"),
            "embedding_models": client.get_models(model_type="embedding"),
        }

    def validate(self):
        pass
