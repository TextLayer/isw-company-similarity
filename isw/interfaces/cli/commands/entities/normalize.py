import click
import numpy as np
from tqdm import tqdm

from isw.core.commands.entity import UpdateEntityCommand
from isw.core.models.entity_models import Entity
from isw.core.services.database import DatabaseService
from isw.core.services.similarity import RevenueSimilarityService


@click.command("normalize-revenue")
@click.option("--n-buckets", type=int, default=20)
@click.option("--force", is_flag=True, help="Recompute all")
def normalize_revenue(n_buckets: int, force: bool):
    """Assign entities to revenue buckets for similarity comparison."""
    db = DatabaseService.get_instance()

    with db.session_scope() as session:
        # Use revenue_usd for normalization (comparable across currencies)
        query = session.query(Entity).filter(Entity.revenue_usd.isnot(None))
        if not force:
            query = query.filter(Entity.norm_tot_rev.is_(None))

        entities_with_revenue = query.all()

        if len(entities_with_revenue) < 2:
            click.echo("Need at least 2 entities with USD revenue.")
            return

        revenues = np.array([e.revenue_usd for e in entities_with_revenue])
        identifiers = [e.identifier for e in entities_with_revenue]

    service = RevenueSimilarityService(n_buckets=n_buckets)
    result = service.compute_similarity(revenues)

    updated = 0
    for identifier, bucket in tqdm(
        zip(identifiers, result.bucket_assignments, strict=True),
        total=len(identifiers),
        desc="Normalizing",
        unit="entity",
    ):
        update_result = UpdateEntityCommand(identifier=identifier, norm_tot_rev=int(bucket)).execute()
        if update_result.updated:
            updated += 1

    click.echo(f"Done. {updated:,} entities assigned to {n_buckets} buckets.")
