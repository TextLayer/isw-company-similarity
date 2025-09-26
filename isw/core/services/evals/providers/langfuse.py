import asyncio
import hashlib
import hmac
from asyncio.log import logger
from typing import Any, Callable, Optional

from langfuse import Langfuse, observe

from .....shared.config import config
from ....utils.helpers import get_header_value
from .base import EvalsProvider, EvalsProviderFactory


class LangfuseProvider(EvalsProvider):
    def __del__(self):
        """Flush the client to ensure all data is sent to the server."""
        self.client.flush()

    def __init__(self):
        conf = config()
        self.client = Langfuse(
            host=conf.langfuse_host,
            public_key=conf.langfuse_public_key,
            secret_key=conf.langfuse_secret_key,
        )

        self.secret = conf.langfuse_signing_secret_prompts
        self.tag = conf.env

    def add_item_to_dataset(self, dataset_name: str, input: Any, output: Any) -> bool:
        """
        Add an item to a dataset.

        Parameters:
            dataset_name: The name of the dataset to add the item to.
            input: The input data for the item.
            output: The expected output of the item.

        Returns:
            True if the item was added successfully, False otherwise.
        """

        self.client.create_dataset_item(
            dataset_name=dataset_name,
            expected_output=output,
            input=input,
        )
        return True

    def create_prompt(self, name: str, content: str) -> bool:
        """
        Create a prompt.

        Parameters:
            name: The name of the prompt to create.
            content: The text content of the prompt.

        """
        self.client.create_prompt(
            labels=[self.tag],
            name=name,
            prompt=content,
            type="text",
        )

        return True

    def create_dataset(self, name: str, description: Optional[str] = None, metadata: Optional[dict] = None) -> bool:
        """
        Create a dataset.

        Parameters:
            name: The name of the dataset to create.
            description: The description of the dataset.
            metadata: The metadata of the dataset.

        Returns:
            True if the dataset was created successfully, False otherwise.
        """
        self.client.create_dataset(
            description=description,
            name=name,
            metadata=metadata,
        )

        return True

    def get_prompts(self) -> list[dict[str, str]]:
        """
        Get all prompts via pagination recursively.
        """
        page = 1
        prompts = []

        while True:
            response = self.client.api.prompts.list(page=page)
            for prompt_meta in response.data:
                try:
                    prompts.append(
                        {
                            "name": prompt_meta.name,
                            "content": self.client.get_prompt(prompt_meta.name, label=self.tag).prompt,
                        }
                    )
                except Exception as e:
                    logger.warning(f"Couldn't list prompt {prompt_meta.name}: {e}")

            if page >= response.meta.total_pages:
                break

            page += 1

        return prompts

    def remove_item_from_dataset(self, dataset_name: str, id: str) -> bool:
        """
        Remove an item from a dataset.
        Langfuse doesn't have an delete method, so it's practically the same as update,
        just with a different status.

        Parameters:
            dataset_name: The name of the dataset to remove the item from.
            id: The id of the item to remove.
        """
        self.client.delete_dataset_item(dataset_name=dataset_name, id=id, status="ARCHIVED")
        return True

    async def run(
        self,
        dataset_name: str,
        run_name: str,
        description: str,
        prompt_lambda: Callable[[str], str],
        concurrency: Optional[int] = 10,
    ):
        """
        Run an evals workflow remotely.

        Parameters:
            dataset_name: The name of the dataset to run the workflow on.
            run_name: The name of the run.
            description: The description of the run.
            prompt_lambda: The lambda function to use for the run.
            concurrency: The concurrency level to use for the run.
        """
        dataset = self.client.get_dataset(dataset_name)
        semaphore = asyncio.Semaphore(concurrency)

        @observe()  # TODO: remove once we're fully instrumented
        async def process_item(item):
            async with semaphore:
                with item.run(run_name=run_name, run_description=description):
                    self.update_trace(item.input, prompt_lambda(item.input))

        tasks = [process_item(item) for item in dataset.items]
        await asyncio.gather(*tasks)

    def upsert_item_to_dataset(self, dataset_name: str, id: str, input: Any, output: Any):
        """
        Upsert an item to a dataset.
        Langfuse doesn't have an update method, so it's practically the same as create.

        Parameters:
            dataset_name: The name of the dataset to upsert the item to.
            id: The id of the item to upsert.
            input: The input data for the item.
            output: The expected output of the item.
        """
        self.client.create_dataset_item(
            dataset_name=dataset_name,
            expected_output=output,
            id=id,
            input=input,
        )

    def update_trace(self, input: Any, output: Any):
        """
        Update the current trace.

        Parameters:
            input: The input data for the trace.
            output: The output data for the trace.
        """
        self.client.update_current_trace(input=input, output=output)

    def validate_webhook_signature(
        self,
        signature: str,
        body: str,
    ) -> bool:
        """
        Validate a Langfuse webhook/event signature.
        SRC: https://langfuse.com/docs/prompt-management/features/webhooks-slack-integrations#verify-authenticity-recommended

        Parameters:
            body: The request body exactly as received (no decoding or reformatting).
            signature: The value of the `Langfuse-Signature` header, e.g. "t=1720701136,s=0123abcd...".

        Returns:
            bool: True if the signature is valid, otherwise False.
        """
        try:
            ts_pair, sig_pair = signature.split(",", 1)
        except ValueError:
            return False

        if "=" not in ts_pair or "=" not in sig_pair:
            return False

        timestamp = get_header_value(ts_pair)
        received_sig_hex = get_header_value(sig_pair)
        message = f"{timestamp}.{body}".encode("utf-8")

        expected_sig_hex = hmac.new(self.secret.encode("utf-8"), message, hashlib.sha256).hexdigest()

        try:
            return hmac.compare_digest(bytes.fromhex(received_sig_hex), bytes.fromhex(expected_sig_hex))
        except ValueError:
            return False


EvalsProviderFactory.register("langfuse", LangfuseProvider)
