from ...commands.base import ReadCommand
from ...errors.validation import ValidationException
from ...models.entity_models import Entity
from ...services.database.service import DatabaseService


class GetEntityCommand(ReadCommand):
    """Get a single entity by identifier."""

    def __init__(self, identifier: str):
        self.identifier = identifier

    def validate(self):
        if not self.identifier:
            raise ValidationException("Identifier is required")

    def execute(self):
        with DatabaseService.get_instance().session_scope() as session:
            entity = session.query(Entity).filter(Entity.identifier == self.identifier).first()
            return entity.to_dict() if entity else None
