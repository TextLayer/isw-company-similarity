from typing import Any, Dict, Generator, List, Optional, Union

from vaul import Toolkit

from ....shared.config import config
from ....shared.logging.logger import logger
from ....templates.prompts import load_prompt
from ...commands.base import WriteCommand
from ...errors import ProcessingException
from ...schemas.thread_schemas import chat_messages_schema
from ...services.llm import ChatClient
from ...tools import TOOL_REGISTRY


class ProcessChatMessageCommand(WriteCommand):
    def __init__(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        max_steps: Optional[int] = None,
        stream: bool = True,
    ):
        self.messages = messages
        self.stream = stream
        self.max_steps = max_steps
        self.model = model

    def validate(self):
        self.__dict__.update(chat_messages_schema.load(self.__dict__))

    def execute(self) -> Union[List[Dict[str, Any]], Generator[str, None, None]]:
        """Start a conversation w/ tools and a system prompt"""
        llm_session = ChatClient(
            models=self._get_models(),
        )

        formatted_messages = [{"role": "system", "content": load_prompt("system")}] + self.messages

        toolkit = Toolkit()
        toolkit.add_tools(*TOOL_REGISTRY)

        try:
            return llm_session.chat(
                max_steps=self.max_steps,
                messages=formatted_messages,
                stream=self.stream,
                tools=toolkit,
            )
        except Exception as e:
            logger.error(f"Failed to fetch chat response: {e}")
            raise ProcessingException("Failed to fetch chat response") from e

    def _get_models(self) -> List[str]:
        """Load models from config and/or model passed as argument"""
        models = config().chat_models
        if self.model and self.model in models:
            return [self.model]

        return models
