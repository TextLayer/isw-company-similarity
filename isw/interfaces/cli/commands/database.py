import click
from sqlalchemy import func

from isw.core.models.entity_models import Entity
from isw.core.services.database import Base, DatabaseService


@click.group()
def database():
    """Database management commands."""
    pass


@database.command()
def init():
    """Initialize database tables."""
    click.echo("Initializing database tables...")
    db = DatabaseService.get_instance()
    Base.metadata.create_all(db.engine)
    click.echo("Tables created")


@database.command()
def status():
    """Show database status."""
    db = DatabaseService.get_instance()

    with db.session_scope() as session:
        entity_count = session.query(Entity).count()

        click.echo(f"\nEntities: {entity_count:,}")


@database.command()
def audit():
    """
    Report data quality metrics.

    Shows detailed statistics about entity data including:
    - Total counts by jurisdiction
    - Enrichment status (description, embedding)
    - Data quality issues

    Examples:

        isw-company-similarity-cli database audit
    """
    db = DatabaseService.get_instance()

    with db.session_scope() as session:
        # Total count
        total = session.query(Entity).count()

        if total == 0:
            click.echo("\nNo entities in database.")
            click.echo("Run 'entities collect' to populate the database.")
            return

        click.echo("\n" + "=" * 50)
        click.echo("DATA QUALITY REPORT")
        click.echo("=" * 50)

        click.echo(f"\nTotal entities: {total:,}")

        # By jurisdiction
        click.echo("\n--- By Jurisdiction ---")
        jurisdiction_counts = (
            session.query(Entity.jurisdiction, func.count(Entity.id))
            .group_by(Entity.jurisdiction)
            .order_by(Entity.jurisdiction)
            .all()
        )
        for jurisdiction, count in jurisdiction_counts:
            pct = 100 * count / total
            click.echo(f"  {jurisdiction}: {count:,} ({pct:.1f}%)")

        # By identifier type
        click.echo("\n--- By Identifier Type ---")
        type_counts = (
            session.query(Entity.identifier_type, func.count(Entity.id))
            .group_by(Entity.identifier_type)
            .order_by(Entity.identifier_type)
            .all()
        )
        for id_type, count in type_counts:
            pct = 100 * count / total
            click.echo(f"  {id_type}: {count:,} ({pct:.1f}%)")

        # Enrichment status
        click.echo("\n--- Enrichment Status ---")
        with_description = session.query(Entity).filter(Entity.description.isnot(None)).count()
        without_description = total - with_description

        click.echo(f"  With description:    {with_description:,} ({100 * with_description / total:.1f}%)")
        click.echo(f"  Missing description: {without_description:,} ({100 * without_description / total:.1f}%)")

        # Embedding status
        click.echo("\n--- Embedding Status ---")
        with_embedding = session.query(Entity).filter(Entity.embedded_description.isnot(None)).count()
        without_embedding = total - with_embedding

        click.echo(f"  With embedding:    {with_embedding:,} ({100 * with_embedding / total:.1f}%)")
        click.echo(f"  Missing embedding: {without_embedding:,} ({100 * without_embedding / total:.1f}%)")

        # Cross-reference: description but no embedding
        desc_no_embed = (
            session.query(Entity)
            .filter(Entity.description.isnot(None))
            .filter(Entity.embedded_description.is_(None))
            .count()
        )
        if desc_no_embed > 0:
            click.echo(f"\n  Warning: {desc_no_embed:,} entities have description but no embedding")

        # Enrichment by jurisdiction
        click.echo("\n--- Enrichment by Jurisdiction ---")
        for jurisdiction, jur_total in jurisdiction_counts:
            jur_enriched = (
                session.query(Entity)
                .filter(Entity.jurisdiction == jurisdiction)
                .filter(Entity.description.isnot(None))
                .count()
            )
            jur_pct = 100 * jur_enriched / jur_total if jur_total > 0 else 0
            click.echo(f"  {jurisdiction}: {jur_enriched:,}/{jur_total:,} enriched ({jur_pct:.1f}%)")

        # Revenue data status
        click.echo("\n--- Revenue Data ---")
        with_revenue = session.query(Entity).filter(Entity.total_revenue.isnot(None)).count()
        click.echo(f"  With revenue data: {with_revenue:,} ({100 * with_revenue / total:.1f}%)")

        # Sample of unenriched entities
        if without_description > 0:
            click.echo("\n--- Sample Unenriched Entities ---")
            samples = (
                session.query(Entity).filter(Entity.description.is_(None)).order_by(Entity.identifier).limit(5).all()
            )
            for entity in samples:
                name = entity.name[:40] if len(entity.name) > 40 else entity.name
                click.echo(f"  {entity.identifier} ({entity.jurisdiction}): {name}")
            if without_description > 5:
                click.echo(f"  ... and {without_description - 5:,} more")

        click.echo("\n" + "=" * 50)
