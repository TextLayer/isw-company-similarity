import click

from isw.core.models.company_models import Company
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
    click.echo("✓ Tables created")


@database.command()
def status():
    """Show database status."""
    db = DatabaseService.get_instance()

    with db.session_scope() as session:
        companies = session.query(Company).count()

        click.echo(f"\nCompanies: {companies:,}")
