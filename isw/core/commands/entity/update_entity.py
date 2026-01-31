from dataclasses import dataclass
from datetime import datetime

from isw.core.commands.base import WriteCommand
from isw.core.models.entity_models import Entity
from isw.core.services.database import DatabaseService


@dataclass
class UpdateEntityInput:
    identifier: str
    name: str | None = None
    description: str | None = None
    embedded_description: list[float] | None = None
    revenue_raw: float | None = None
    revenue_currency: str | None = None
    revenue_usd: float | None = None
    revenue_period_end: str | None = None
    revenue_source_tags: list[str] | None = None
    norm_tot_rev: int | None = None


@dataclass
class UpdateEntityResult:
    identifier: str
    updated: bool
    not_found: bool = False


class UpdateEntityCommand(WriteCommand):
    """Update an existing entity's attributes."""

    def __init__(
        self,
        identifier: str,
        name: str | None = None,
        description: str | None = None,
        embedded_description: list[float] | None = None,
        revenue_raw: float | None = None,
        revenue_currency: str | None = None,
        revenue_usd: float | None = None,
        revenue_period_end: str | None = None,
        revenue_source_tags: list[str] | None = None,
        norm_tot_rev: int | None = None,
    ):
        self.input = UpdateEntityInput(
            identifier=identifier,
            name=name,
            description=description,
            embedded_description=embedded_description,
            revenue_raw=revenue_raw,
            revenue_currency=revenue_currency,
            revenue_usd=revenue_usd,
            revenue_period_end=revenue_period_end,
            revenue_source_tags=revenue_source_tags,
            norm_tot_rev=norm_tot_rev,
        )

    def validate(self):
        from isw.core.errors.validation import ValidationException

        if not self.input.identifier:
            raise ValidationException("Entity identifier is required")

    def execute(self) -> UpdateEntityResult:
        db = DatabaseService.get_instance()
        updated = False

        with db.session_scope() as session:
            entity = session.query(Entity).filter(Entity.identifier == self.input.identifier).first()

            if not entity:
                return UpdateEntityResult(
                    identifier=self.input.identifier,
                    updated=False,
                    not_found=True,
                )

            if self.input.name is not None:
                entity.name = self.input.name
                updated = True

            if self.input.description is not None:
                entity.description = self.input.description
                updated = True

            if self.input.embedded_description is not None:
                entity.embedded_description = self.input.embedded_description
                updated = True

            if self.input.revenue_raw is not None:
                entity.revenue_raw = self.input.revenue_raw
                updated = True

            if self.input.revenue_currency is not None:
                entity.revenue_currency = self.input.revenue_currency
                updated = True

            if self.input.revenue_usd is not None:
                entity.revenue_usd = self.input.revenue_usd
                updated = True

            if self.input.revenue_period_end is not None:
                entity.revenue_period_end = self.input.revenue_period_end
                updated = True

            if self.input.revenue_source_tags is not None:
                entity.revenue_source_tags = self.input.revenue_source_tags
                updated = True

            if self.input.norm_tot_rev is not None:
                entity.norm_tot_rev = self.input.norm_tot_rev
                updated = True

            if updated:
                entity.updated_at = datetime.utcnow()

        return UpdateEntityResult(identifier=self.input.identifier, updated=updated)
