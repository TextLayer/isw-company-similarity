from abc import ABC, abstractmethod
from typing import Any, Callable, Optional

from ....utils.factory import GenericProviderFactory


class EvalsProvider(ABC):
    @abstractmethod
    def add_item_to_dataset(self, dataset_name: str, input: Any, output: Any) -> bool:
        pass

    @abstractmethod
    def create_dataset(self, name: str, description: Optional[str] = None, metadata: Optional[dict] = None) -> bool:
        pass

    @abstractmethod
    def create_prompt(self, name: str, content: str) -> bool:
        pass

    @abstractmethod
    def get_prompts(self) -> list[dict[str, str]]:
        pass

    @abstractmethod
    def remove_item_from_dataset(self, dataset_name: str, id: str) -> bool:
        pass

    @abstractmethod
    def run(
        self,
        dataset_name: str,
        run_name: str,
        description: str,
        prompt_lambda: Callable[[str], str],
        concurrency: Optional[int],
    ):
        pass

    @abstractmethod
    def upsert_item_to_dataset(self, dataset_name: str, id: str, input: Any, output: Any) -> bool:
        pass

    @abstractmethod
    def update_trace(self, input: Any, output: Any):
        pass


EvalsProviderFactory = GenericProviderFactory[EvalsProvider]("evals")
