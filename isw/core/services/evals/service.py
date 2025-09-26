from typing import Any, Optional

from ....shared.config import config
from ....shared.logging.logger import logger
from ...errors.service import ServiceException
from ...utils.helpers import to_snake_case
from .providers import EvalsProviderFactory


class EvalsService:
    def __init__(self, provider: Optional[str] = None, **kwargs):
        """
        Initialize the EvalsService class.

        Parameters:
            provider: The provider to use for the evals.
            **kwargs: Additional arguments to pass to the provider.
        """
        self.provider = EvalsProviderFactory.create(
            provider or config().evals_provider,
            **kwargs,
        )

    def add_item_to_dataset(self, dataset_name: str, input: Any, output: Any) -> bool:
        """
        Add an item to a dataset.

        Parameters:
            dataset_name: The name of the dataset to add the item to.
            input: The input data for the item.
            output: The expected output of the item.

        Returns:
            True if the item was added successfully, otherwise raises an exception.
        """
        try:
            return self.provider.add_item_to_dataset(to_snake_case(dataset_name), input, output)
        except Exception as e:
            logger.error(f"Error adding item to dataset: {e}")
            raise ServiceException("Could not add item to dataset") from e

    def create_dataset(self, name: str, description: Optional[str] = None, metadata: Optional[dict] = None) -> bool:
        """
        Create a dataset.

        Parameters:
            name: The name of the dataset to create.
            description: The description of the dataset.
            metadata: The metadata of the dataset.

        Returns:
            True if the dataset was created successfully, otherwise raises an exception.
        """
        try:
            return self.provider.create_dataset(to_snake_case(name), description, metadata)
        except Exception as e:
            logger.error(f"Error creating dataset: {e}")
            raise ServiceException("Could not create dataset") from e

    def create_prompt(self, name: str, content: str) -> bool:
        """
        Create a prompt.
        """
        try:
            return self.provider.create_prompt(to_snake_case(name), content)
        except Exception as e:
            logger.error(f"Error creating prompt: {e}")
            raise ServiceException("Could not create prompt") from e

    def get_prompts(self) -> list[dict[str, str]]:
        """
        Get all prompts.
        """
        try:
            return self.provider.get_prompts()
        except Exception as e:
            logger.error(f"Error getting prompts: {e}")
            raise ServiceException("Could not get prompts") from e

    def remove_item_from_dataset(self, dataset_name: str, id: str) -> bool:
        """
        Remove an item from a dataset.

        Parameters:
            dataset_name: The name of the dataset to remove the item from.
            id: The id of the item to remove.

        Returns:
            True if the item was removed successfully, otherwise raises an exception.
        """
        try:
            return self.provider.remove_item_from_dataset(to_snake_case(dataset_name), to_snake_case(id))
        except Exception as e:
            logger.error(f"Error removing item from dataset: {e}")
            raise ServiceException("Could not remove item from dataset") from e

    async def run(self, dataset_name: str, name: str, **kwargs):
        """
        Run a dataset.

        Parameters:
            dataset_name: The name of the dataset to run.
            name: The name of the run.
            **kwargs: Additional arguments to pass to the provider.
        """
        try:
            return await self.provider.run(to_snake_case(dataset_name), to_snake_case(name), **kwargs)
        except Exception as e:
            logger.error(f"Error running dataset: {e}")
            raise ServiceException("Could not run dataset") from e

    def upsert_item_to_dataset(self, dataset_name: str, id: str, input: Any, output: Any) -> bool:
        """
        Upsert an item to a dataset.

        Parameters:
            dataset_name: The name of the dataset to upsert the item to.
            id: The id of the item to upsert.
            input: The input data for the item.
            output: The expected output of the item.

        Returns:
            True if the item was upserted successfully, otherwise raises an exception.
        """
        try:
            return self.provider.upsert_item_to_dataset(to_snake_case(dataset_name), to_snake_case(id), input, output)
        except Exception as e:
            logger.error(f"Error upserting item to dataset: {e}")
            raise ServiceException("Could not upsert item to dataset") from e

    def update_trace(self, input: Any, output: Any):
        """
        Update the current trace.

        Parameters:
            input: The input data for the trace.
            output: The output data for the trace.
        """
        try:
            return self.provider.update_trace(input, output)
        except Exception as e:
            logger.error(f"Error updating trace: {e}")
            raise ServiceException("Could not update trace") from e

    def validate_webhook_signature(self, signature: str, body: str) -> bool:
        """
        Validate the signature of the webhook.
        """
        return self.provider.validate_webhook_signature(
            signature=signature,
            body=body,
        )
