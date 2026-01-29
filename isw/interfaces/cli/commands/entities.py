"""CLI commands for entity collection."""

import json
from pathlib import Path

import click

from isw.core.services.entity_collection import (
    EntityRecord,
    ESEFCollector,
    SECEdgarCollector,
)
from isw.shared.logging.logger import logger


@click.group()
def entities():
    """Entity collection commands."""
    pass


@entities.command()
@click.option(
    "--output",
    "-o",
    type=click.Path(dir_okay=False, writable=True),
    help="Output file path for JSON export.",
)
@click.option(
    "--source",
    "-s",
    type=click.Choice(["all", "sec", "esef"], case_sensitive=False),
    default="all",
    help="Data source to collect from (default: all).",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be collected without actually fetching.",
)
def collect(
    output: str | None,
    source: str,
    dry_run: bool,
):
    """
    Collect entity master list from data sources.

    Fetches company information (name, identifier, jurisdiction) from
    SEC EDGAR (US) and filings.xbrl.org (EU/UK), outputting to JSON.

    The SEC User-Agent is configured via SEC_USER_AGENT environment
    variable or defaults to the value in config.

    Examples:

        # Collect all entities and output to file
        isw-company-similarity-cli entities collect --output entities.json

        # Collect only from SEC EDGAR
        isw-company-similarity-cli entities collect --source sec --output us_entities.json

        # Collect only from ESEF
        isw-company-similarity-cli entities collect --source esef --output eu_entities.json
    """
    if dry_run:
        click.echo("Dry run mode - would collect from:")
        if source in ("all", "sec"):
            click.echo("  - SEC EDGAR (US companies with 10-K filings)")
        if source in ("all", "esef"):
            click.echo("  - filings.xbrl.org (EU/UK ESEF filers)")
        return

    all_entities: list[EntityRecord] = []

    if source in ("all", "sec"):
        click.echo("Collecting from SEC EDGAR...")
        try:
            sec_collector = SECEdgarCollector()
            sec_entities = sec_collector.fetch_entities()
            all_entities.extend(sec_entities)
            click.echo(f"  Collected {len(sec_entities):,} US entities")
        except Exception as e:
            logger.error(f"SEC EDGAR collection failed: {e}")
            click.echo(f"  SEC EDGAR collection failed: {e}", err=True)
            raise click.Abort() from None

    if source in ("all", "esef"):
        click.echo("Collecting from filings.xbrl.org...")
        try:
            esef_collector = ESEFCollector()
            esef_entities = esef_collector.fetch_entities()
            all_entities.extend(esef_entities)
            click.echo(f"  Collected {len(esef_entities):,} EU/UK entities")
        except Exception as e:
            logger.error(f"ESEF collection failed: {e}")
            click.echo(f"  ESEF collection failed: {e}", err=True)
            raise click.Abort() from None

    seen_identifiers: set[str] = set()
    unique_entities: list[EntityRecord] = []
    duplicates = 0

    for entity in all_entities:
        if entity.identifier not in seen_identifiers:
            seen_identifiers.add(entity.identifier)
            unique_entities.append(entity)
        else:
            duplicates += 1

    click.echo(f"\nTotal: {len(unique_entities):,} unique entities")
    if duplicates > 0:
        click.echo(f"  (removed {duplicates:,} duplicates)")

    if output:
        _write_json_output(unique_entities, output)
        click.echo(f"\nSaved to {output}")
    else:
        _print_summary(unique_entities)


def _write_json_output(entities: list[EntityRecord], output_path: str) -> None:
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    data = [entity.to_dict() for entity in entities]

    with open(output_file, "w") as f:
        json.dump(data, f, indent=2)


def _print_summary(entities: list[EntityRecord]) -> None:
    by_jurisdiction: dict[str, int] = {}
    by_type: dict[str, int] = {}

    for entity in entities:
        jurisdiction = entity.jurisdiction.value
        id_type = entity.identifier_type.value

        by_jurisdiction[jurisdiction] = by_jurisdiction.get(jurisdiction, 0) + 1
        by_type[id_type] = by_type.get(id_type, 0) + 1

    click.echo("\nBy jurisdiction:")
    for jurisdiction, count in sorted(by_jurisdiction.items()):
        click.echo(f"  {jurisdiction}: {count:,}")

    click.echo("\nBy identifier type:")
    for id_type, count in sorted(by_type.items()):
        click.echo(f"  {id_type}: {count:,}")
