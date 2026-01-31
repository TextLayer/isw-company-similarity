from isw.core.commands.entity import (
    AddEntityCommand,
    AddEntityResult,
    DeleteEntityCommand,
    DeleteEntityResult,
    GetEntitiesCommand,
    GetEntityCommand,
    SearchEntitiesCommand,
    UpdateEntityCommand,
    UpdateEntityResult,
)
from isw.core.services.entities import EntityRecord

from .base import Controller


class EntityController(Controller):
    """Controller for entity CRUD operations."""

    def search_entities(self, **kwargs):
        command = SearchEntitiesCommand(**kwargs)
        return self.executor.execute_read(command)

    def get_entities(self, **kwargs):
        command = GetEntitiesCommand(**kwargs)
        return self.executor.execute_read(command)

    def get_entity(self, **kwargs):
        command = GetEntityCommand(**kwargs)
        return self.executor.execute_read(command)

    def add_entity(self, record: EntityRecord) -> AddEntityResult:
        command = AddEntityCommand(record=record)
        return self.executor.execute_write(command)

    def update_entity(self, **kwargs) -> UpdateEntityResult:
        command = UpdateEntityCommand(**kwargs)
        return self.executor.execute_write(command)

    def delete_entity(self, identifier: str) -> DeleteEntityResult:
        command = DeleteEntityCommand(identifier=identifier)
        return self.executor.execute_write(command)
