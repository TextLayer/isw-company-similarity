import click
from tqdm import tqdm

from isw.core.commands.entity import AddEntityCommand
from isw.core.services.entities import EntityService


@click.command()
@click.option(
    "--source",
    type=click.Choice(["all", "edgar", "esef"]),
    default="all",
    help="Data source to collect from",
)
@click.option("--limit", type=int, default=None, help="Maximum entities to collect")
def collect(source: str, limit: int | None):
    """Collect entities from SEC EDGAR and/or filings.xbrl.org."""
    service = EntityService()
    entities_to_add = []

    if source in ("all", "edgar"):
        click.echo("Fetching from SEC EDGAR...")
        entities_to_add.extend(service.discover_edgar_entities())

    if source in ("all", "esef"):
        click.echo("Fetching from filings.xbrl.org...")
        # Pass limit to ESEF to avoid fetching thousands of pages
        entities_to_add.extend(service.discover_esef_entities(limit=limit))

    # Deduplicate
    seen = set()
    unique = []
    for e in entities_to_add:
        if e.identifier not in seen:
            seen.add(e.identifier)
            unique.append(e)
    entities_to_add = unique

    if limit:
        entities_to_add = entities_to_add[:limit]

    click.echo(f"Adding {len(entities_to_add):,} entities...")

    added = 0
    for record in tqdm(entities_to_add, desc="Adding", unit="entity"):
        result = AddEntityCommand(record=record).execute()
        if result.created:
            added += 1

    click.echo(f"Done. Added {added:,} new entities.")
