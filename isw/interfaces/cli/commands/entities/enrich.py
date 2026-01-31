import click
from tqdm import tqdm

from isw.core.commands.entity import UpdateEntityCommand
from isw.core.models.entity_models import Entity
from isw.core.services.database import DatabaseService
from isw.core.services.embeddings import EmbeddingService, EmbeddingServiceError
from isw.core.services.entities import EntityService, EntityServiceConfig
from isw.core.services.exchange_rate import ExchangeRateService
from isw.core.services.exchange_rate.base import ExchangeRateError
from isw.shared.config import get_config
from isw.shared.logging.logger import logger


@click.command()
@click.option("-j", "--jurisdiction", type=click.Choice(["US", "EU", "UK"], case_sensitive=False))
@click.option("--limit", type=int, default=None)
@click.option("--force", is_flag=True, help="Overwrite existing data")
@click.option("--skip-descriptions", is_flag=True)
@click.option("--skip-embeddings", is_flag=True)
@click.option("--skip-revenue", is_flag=True)
@click.option("--no-llm", is_flag=True)
def enrich(
    jurisdiction: str | None,
    limit: int | None,
    force: bool,
    skip_descriptions: bool,
    skip_embeddings: bool,
    skip_revenue: bool,
    no_llm: bool,
):
    """Enrich entities with descriptions, embeddings, and revenue.

    By default, only populates missing fields. Use --force to overwrite existing data.
    """
    db = DatabaseService.get_instance()
    config = get_config()

    # Query entities that need enrichment (missing any data)
    with db.session_scope() as session:
        query = session.query(Entity)
        if jurisdiction:
            query = query.filter(Entity.jurisdiction == jurisdiction.upper())

        # If not forcing, only get entities missing some data
        if not force:
            query = query.filter(
                (Entity.description.is_(None))
                | (Entity.embedded_description.is_(None))
                | (Entity.revenue_raw.is_(None))
            )

        if limit:
            query = query.limit(limit)

        entities_to_enrich = [
            {
                "identifier": e.identifier,
                "name": e.name,
                "jurisdiction": e.jurisdiction,
                "has_description": e.description is not None,
                "has_embedding": e.embedded_description is not None,
                "has_revenue": e.revenue_raw is not None,
            }
            for e in query.all()
        ]

    if not entities_to_enrich:
        click.echo("No entities to enrich.")
        return

    entity_service = EntityService(
        config=EntityServiceConfig(
            sec_user_agent=config.sec_user_agent,
            use_ai_extraction=not no_llm,
            use_web_search_fallback=True,
        )
    )
    embedding_service = None
    if not skip_embeddings and config.openai_api_key:
        embedding_service = EmbeddingService(api_key=config.openai_api_key)

    exchange_service = ExchangeRateService() if not skip_revenue else None

    success = 0
    skipped = 0
    errors = 0

    for entity in tqdm(entities_to_enrich, desc="Enriching", unit="entity"):
        try:
            identifier = entity["identifier"]
            updates = {}

            # Only fetch description if missing or forcing
            need_description = force or not entity["has_description"]
            need_embedding = force or not entity["has_embedding"]
            need_revenue = force or not entity["has_revenue"]

            if not skip_descriptions and need_description:
                desc = entity_service.get_business_description(
                    identifier,
                    company_name=entity["name"],
                    country=entity["jurisdiction"],
                )
                if desc:
                    updates["description"] = desc.text

                    # Generate embedding if we have new description
                    if not skip_embeddings and embedding_service:
                        try:
                            embedding = embedding_service.embed_text(desc.text[:8000])
                            updates["embedded_description"] = embedding
                        except EmbeddingServiceError as e:
                            logger.warning(f"Embedding failed for {identifier}: {e}")

            # Generate embedding for existing description if missing
            elif not skip_embeddings and need_embedding and entity["has_description"]:
                if embedding_service:
                    with db.session_scope() as session:
                        e = session.query(Entity).filter(Entity.identifier == identifier).first()
                        if e and e.description:
                            try:
                                embedding = embedding_service.embed_text(e.description[:8000])
                                updates["embedded_description"] = embedding
                            except EmbeddingServiceError as err:
                                logger.warning(f"Embedding failed for {identifier}: {err}")

            if not skip_revenue and need_revenue:
                revenue = entity_service.get_revenue(identifier)
                if revenue:
                    updates["revenue_raw"] = float(revenue.amount)
                    updates["revenue_currency"] = revenue.currency
                    updates["revenue_period_end"] = revenue.period_end
                    updates["revenue_source_tags"] = [revenue.source_tag]

                    # Convert to USD using exchange rates
                    if revenue.currency == "USD":
                        updates["revenue_usd"] = float(revenue.amount)
                    elif exchange_service:
                        try:
                            # Use period end date for historical rate if available
                            date = revenue.period_end if revenue.period_end else None
                            usd_amount = exchange_service.convert_to_usd(
                                float(revenue.amount),
                                revenue.currency,
                                date=date,
                            )
                            updates["revenue_usd"] = usd_amount
                        except (ExchangeRateError, ValueError) as e:
                            logger.warning(f"Currency conversion failed for {identifier}: {e}")

            if updates:
                UpdateEntityCommand(identifier=identifier, **updates).execute()
                success += 1
            else:
                skipped += 1

        except Exception as e:
            logger.warning(f"Error enriching {entity['identifier']}: {e}")
            errors += 1

    click.echo(f"Done. {success:,} enriched, {skipped:,} skipped, {errors:,} errors.")
