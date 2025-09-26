import asyncio
import json

from ....shared.logging.logger import logger
from ...commands.base import WriteCommand
from ...errors import ProcessingException
from ...schemas.workflows_schemas import EvalsWorkflowData, evals_workflow_schema
from ...services.evals import EvalsService


class RunEvalsWorkflowCommand(WriteCommand):
    def __init__(self, **kwargs: EvalsWorkflowData):
        self.__dict__.update(kwargs)

    def validate(self):
        evals_workflow_schema.load(self.__dict__)

    def execute(self):
        """Run an evals workflow synchronously."""
        try:
            asyncio.run(
                EvalsService().run(
                    dataset_name=self.runner,
                    name=self.name,
                    description=self.description,
                    prompt_lambda=lambda input_data: (json.dumps(self.prompt(input_data))),
                )
            )
        except Exception as e:
            logger.error(f"Error in evals workflow: {e}")
            raise ProcessingException("Eval workflow failed to complete") from e
