import click

from .collect import collect
from .enrich import enrich
from .normalize import normalize_revenue


@click.group()
def entities():
    """Manage entity collection and enrichment."""
    pass


entities.add_command(collect)
entities.add_command(enrich)
entities.add_command(normalize_revenue)
