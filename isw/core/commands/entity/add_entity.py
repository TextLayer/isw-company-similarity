from dataclasses import dataclass
from datetime import datetime

from isw.core.commands.base import WriteCommand
from isw.core.models.entity_models import Entity
from isw.core.services.database import DatabaseService
from isw.core.services.entities import EntityRecord


@dataclass
class AddEntityInput:
    record: EntityRecord


@dataclass
class AddEntityResult:
    identifier: str
    created: bool
    updated: bool = False


class AddEntityCommand(WriteCommand):
    """Add a single entity to the database. Returns existing if already present."""

    def __init__(self, record: EntityRecord):
        self.input = AddEntityInput(record=record)

    def validate(self):
        from isw.core.errors.validation import ValidationException

        if not self.input.record.identifier:
            raise ValidationException("Entity identifier is required")
        if not self.input.record.name:
            raise ValidationException("Entity name is required")

    def execute(self) -> AddEntityResult:
        db = DatabaseService.get_instance()
        record = self.input.record

        with db.session_scope() as session:
            existing = session.query(Entity).filter(Entity.identifier == record.identifier).first()

            if existing:
                return AddEntityResult(
                    identifier=record.identifier,
                    created=False,
                    updated=False,
                )

            entity = Entity(
                identifier=record.identifier,
                identifier_type=record.identifier_type.value,
                jurisdiction=record.jurisdiction.value,
                name=record.name,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            session.add(entity)

        return AddEntityResult(identifier=record.identifier, created=True)
