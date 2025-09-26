import click

from isw.core.controllers.recruitment_controller import RecruitmentController

from .cli import cli

controller = RecruitmentController()


@cli.command(name="create-jobs-index")
def create_jobs_index():
    try:
        controller.create_jobs_index()
        click.secho("The jobs index has been created successfully!", fg="green")
    except Exception as e:
        click.secho(f'Sorry, but the jobs index could not be created. Reason: "{e}".', fg="red")
