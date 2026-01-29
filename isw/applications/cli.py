import click

from isw.interfaces.cli.commands.database import database
from isw.interfaces.cli.commands.entities import entities
from isw.shared.config import set_config
from isw.shared.config.cli_adapter import get_cli_config


@click.group()
def cli():
    """ISW Company Similarity CLI"""
    pass


set_config(get_cli_config())

# Register command groups
cli.add_command(database)
cli.add_command(entities)
