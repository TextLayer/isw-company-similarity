import csv
import json

import click

from ...core.controllers.recruitment_controller import RecruitmentController
from ...core.controllers.workflows_controller import WorkflowsController
from ...core.services.evals import EvalsService
from ...core.utils.helpers import from_json
from .cli import cli


@cli.command(name="add-evals-dataset-item")
@click.argument("name", type=str)
@click.argument("file", type=str)
def add_evals_dataset_item(
    name: str,
    file: str,
):
    """
    Upsert items to a dataset based on a file uploaded to the .tmp folder.
    To be run from terminal -- little file validation given in this script.

    Parameters:
        file: The file to upsert items from. Should be a CSV with headers:
            - itemid_id: The ID of the item in the dataset
            - output: The expected output of the item after evaluation
            - *other columns: The input data for the item, serialized as JSON
        name: The name of the dataset to upsert items to
    """
    try:
        with open(f".tmp/{file}", "r", newline="", encoding="utf-8") as file_data:
            csv_reader = csv.DictReader(file_data)

            for row in csv_reader:
                id = row.pop("id")
                input = {}
                output = row.pop("output")

                for key, value in row.items():
                    # might be double-encoded
                    input[key] = from_json(from_json(value))

                EvalsService().upsert_item_to_dataset(
                    dataset_name=name,
                    id=id,
                    input=json.dumps(input),
                    output=output,
                )

        click.secho("Datasets uploaded successfully!", fg="green")
    except Exception as e:
        click.secho(f'Sorry, but the evals dataset could not be uploaded. Reason: "{e}".', fg="red")


@cli.command(name="create-evals-dataset")
@click.argument("name", type=str)
@click.argument("description", type=str)
def create_evals_dataset(name: str, description: str):
    """
    Create a new evals dataset.

    Parameters:
        name: The name of the dataset to create
        description: The description of the dataset
    """
    try:
        EvalsService().create_dataset(
            name=name,
            description=description,
        )
        click.secho("The evals dataset has been created successfully!", fg="green")
    except Exception as e:
        click.secho(f'Sorry, but the evals dataset could not be created. Reason: "{e}".', fg="red")


@cli.command(name="run-evals-workflow")
@click.argument("name", type=str)
@click.argument("description", type=str)
@click.argument("runner", type=str)
def run_evals_workflow(name: str, description: str, runner: str):
    """
    Run an evals workflow remotely.
    Likely, used in CI/CD on demand.

    Parameters:
        name: The name of the workflow to run
        description: The description of the workflow
        runner: The runner of the workflow
    """
    try:
        recruitment_controller = RecruitmentController()

        WorkflowsController().run_evals(
            name=name,
            description=description,
            runner=runner,
            prompt=lambda input_data: (recruitment_controller.analyze_candidate_resume(**json.loads(input_data))),
        )
        click.secho("The evals workflow has been run successfully!", fg="green")
    except Exception as e:
        click.secho(f'Sorry, but the evals workflow could not be run. Reason: "{e}".', fg="red")


@cli.command(name="sync-prompts")
@click.argument("provider_name", type=str, required=False)
def sync_prompts(provider_name: str):
    """
    Sync prompts with the service provider.
    """
    try:
        WorkflowsController().sync_prompts(provider_name)
        click.secho("The prompts have been synced successfully!", fg="green")
    except Exception as e:
        click.secho(f'Sorry, but the prompts could not be synced. Reason: "{e}".', fg="red")


@cli.command(name="update-prompts")
@click.argument("provider_name", type=str, required=False)
def update_prompts(provider_name: str):
    """
    Update prompts with the service provider.
    """
    try:
        WorkflowsController().update_prompts(provider_name)
        click.secho("The prompts have been updated successfully!", fg="green")
    except Exception as e:
        click.secho(f'Sorry, but the prompts could not be updated. Reason: "{e}".', fg="red")
