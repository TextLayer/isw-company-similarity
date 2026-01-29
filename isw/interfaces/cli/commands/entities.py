"""CLI commands for entity collection and enrichment."""

import json
import time
from dataclasses import dataclass
from pathlib import Path

import click

from isw.core.services.data_sources import DataSourceFactory
from isw.core.services.embeddings import EmbeddingService, EmbeddingServiceError
from isw.core.services.entity_collection import (
    EntityRecord,
    ESEFCollector,
    SECEdgarCollector,
)
from isw.shared.config import get_config
from isw.shared.logging.logger import logger


@dataclass
class EnrichedEntity:
    """Entity enriched with business description and embedding."""

    name: str
    identifier: str
    jurisdiction: str
    identifier_type: str
    business_description: str | None = None
    embedding: list[float] | None = None
    enrichment_error: str | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        result = {
            "name": self.name,
            "identifier": self.identifier,
            "jurisdiction": self.jurisdiction,
            "identifier_type": self.identifier_type,
        }
        if self.business_description is not None:
            result["business_description"] = self.business_description
        if self.embedding is not None:
            result["embedding"] = self.embedding
        if self.enrichment_error is not None:
            result["enrichment_error"] = self.enrichment_error
        return result


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


@entities.command()
@click.option(
    "--input",
    "-i",
    "input_file",
    type=click.Path(exists=True, dir_okay=False, readable=True),
    required=True,
    help="Input JSON file with entities (from 'collect' command).",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(dir_okay=False, writable=True),
    required=True,
    help="Output file path for enriched entities JSON.",
)
@click.option(
    "--limit",
    "-l",
    type=int,
    default=None,
    help="Limit the number of entities to process (for testing).",
)
@click.option(
    "--skip-embeddings",
    is_flag=True,
    help="Skip embedding generation (only fetch descriptions).",
)
@click.option(
    "--delay",
    type=float,
    default=0.5,
    help="Delay between API calls in seconds (default: 0.5).",
)
@click.option(
    "--resume-from",
    type=int,
    default=0,
    help="Resume processing from this entity index (0-based).",
)
def enrich(
    input_file: str,
    output: str,
    limit: int | None,
    skip_embeddings: bool,
    delay: float,
    resume_from: int,
):
    """
    Enrich entities with business descriptions and embeddings.

    Reads entities from JSON file (output from 'collect' command),
    fetches business descriptions from SEC EDGAR / filings.xbrl.org,
    generates embeddings using OpenAI, and outputs enriched data.

    Requires OPENAI_API_KEY environment variable for embeddings.

    Examples:

        # Enrich all entities
        isw-company-similarity-cli entities enrich -i entities.json -o enriched.json

        # Test with first 10 entities
        isw-company-similarity-cli entities enrich -i entities.json -o test.json --limit 10

        # Skip embeddings (only fetch descriptions)
        isw-company-similarity-cli entities enrich -i entities.json -o desc.json --skip-embeddings

        # Resume from entity 100 (if previous run failed)
        isw-company-similarity-cli entities enrich -i entities.json -o enriched.json --resume-from 100
    """
    config = get_config()

    # Load entities from input file
    click.echo(f"Loading entities from {input_file}...")
    with open(input_file) as f:
        raw_entities = json.load(f)

    entities = [EntityRecord.from_dict(e) for e in raw_entities]
    total_loaded = len(entities)
    click.echo(f"Loaded {total_loaded:,} entities")

    # Apply resume offset first
    if resume_from > 0:
        entities = entities[resume_from:]
        click.echo(f"Resuming from index {resume_from} ({len(entities):,} remaining)")

    # Apply limit after resume
    if limit is not None:
        entities = entities[:limit]
        click.echo(f"Processing {len(entities):,} entities (--limit)")

    # Track the count of entities we're actually processing
    processing_count = len(entities)

    # Initialize services
    click.echo("\nInitializing services...")
    try:
        factory = DataSourceFactory(sec_user_agent=config.sec_user_agent)
        click.echo("  DataSourceFactory initialized")
    except Exception as e:
        click.echo(f"  Failed to initialize DataSourceFactory: {e}", err=True)
        raise click.Abort() from None

    embedding_service = None
    if not skip_embeddings:
        if not config.openai_api_key:
            click.echo("  OPENAI_API_KEY not set - use --skip-embeddings or set the key", err=True)
            raise click.Abort() from None
        try:
            embedding_service = EmbeddingService(
                api_key=config.openai_api_key,
                model=config.openai_embedding_model,
            )
            click.echo(f"  EmbeddingService initialized (model: {config.openai_embedding_model})")
        except EmbeddingServiceError as e:
            click.echo(f"  Failed to initialize EmbeddingService: {e}", err=True)
            raise click.Abort() from None

    # Process entities
    enriched_entities: list[EnrichedEntity] = []
    success_count = 0
    error_count = 0
    no_description_count = 0

    click.echo(f"\nEnriching {len(entities):,} entities...")
    click.echo("-" * 60)

    for i, entity in enumerate(entities):
        progress = f"[{i + 1}/{processing_count}]"

        try:
            # Fetch business description
            description = factory.get_business_description(entity.identifier)

            if description is None:
                no_description_count += 1
                enriched = EnrichedEntity(
                    name=entity.name,
                    identifier=entity.identifier,
                    jurisdiction=entity.jurisdiction.value,
                    identifier_type=entity.identifier_type.value,
                    enrichment_error="No business description available",
                )
                enriched_entities.append(enriched)
                click.echo(f"{progress} {entity.name[:40]:<40} - No description")
                continue

            # Generate embedding if enabled
            embedding = None
            if embedding_service is not None:
                try:
                    embedding = embedding_service.embed_text(description.text[:8000])
                except EmbeddingServiceError as e:
                    logger.warning(f"Embedding failed for {entity.identifier}: {e}")

            enriched = EnrichedEntity(
                name=entity.name,
                identifier=entity.identifier,
                jurisdiction=entity.jurisdiction.value,
                identifier_type=entity.identifier_type.value,
                business_description=description.text,
                embedding=embedding,
            )
            enriched_entities.append(enriched)
            success_count += 1

            status = "enriched"
            if embedding is None and not skip_embeddings:
                status = "desc only (embedding failed)"
            click.echo(f"{progress} {entity.name[:40]:<40} - {status}")

        except Exception as e:
            error_count += 1
            enriched = EnrichedEntity(
                name=entity.name,
                identifier=entity.identifier,
                jurisdiction=entity.jurisdiction.value,
                identifier_type=entity.identifier_type.value,
                enrichment_error=str(e),
            )
            enriched_entities.append(enriched)
            logger.error(f"Failed to enrich {entity.identifier}: {e}")
            click.echo(f"{progress} {entity.name[:40]:<40} - ERROR: {str(e)[:30]}")

        # Rate limiting
        if delay > 0 and i < len(entities) - 1:
            time.sleep(delay)

    # Write output
    click.echo("-" * 60)
    click.echo(f"\nWriting {len(enriched_entities):,} entities to {output}...")

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump([e.to_dict() for e in enriched_entities], f, indent=2)

    # Summary
    click.echo("\nSummary:")
    click.echo(f"  Successfully enriched: {success_count:,}")
    click.echo(f"  No description found:  {no_description_count:,}")
    click.echo(f"  Errors:                {error_count:,}")
    click.echo(f"\nOutput saved to {output}")
