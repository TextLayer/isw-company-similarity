from dataclasses import dataclass

from isw.core.commands.base import WriteCommand
from isw.core.models.entity_models import Entity
from isw.core.services.database import DatabaseService


@dataclass
class DeleteEntityInput:
    identifier: str


@dataclass
class DeleteEntityResult:
    identifier: str
    deleted: bool
    not_found: bool = False


class DeleteEntityCommand(WriteCommand):
    """Delete an entity from the database."""

    def __init__(self, identifier: str):
        self.input = DeleteEntityInput(identifier=identifier)

    def validate(self):
        from isw.core.errors.validation import ValidationException

        if not self.input.identifier:
            raise ValidationException("Entity identifier is required")

    def execute(self) -> DeleteEntityResult:
        db = DatabaseService.get_instance()

        with db.session_scope() as session:
            entity = session.query(Entity).filter(Entity.identifier == self.input.identifier).first()

            if not entity:
                return DeleteEntityResult(
                    identifier=self.input.identifier,
                    deleted=False,
                    not_found=True,
                )

            session.delete(entity)

        return DeleteEntityResult(identifier=self.input.identifier, deleted=True)
