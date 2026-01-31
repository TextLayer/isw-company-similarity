from sqlalchemy import select

from isw.core.commands.base import ReadCommand
from isw.core.errors.validation import ValidationException
from isw.core.models.entity_models import Entity
from isw.core.services.database import DatabaseService


class SearchEntitiesCommand(ReadCommand):
    """Search entities by embedding similarity."""

    def __init__(
        self,
        identifier: str,
        similarity_threshold: float = 0.7,
        max_results: int = 10,
        filter_community: bool = True,
    ):
        self.identifier = identifier
        self.similarity_threshold = similarity_threshold
        self.max_results = max_results
        self.filter_community = filter_community

    def validate(self) -> bool:
        if not self.identifier:
            raise ValidationException("Identifier is required")
        return True

    def execute(self):
        with DatabaseService.get_instance().session_scope() as session:
            entity = session.query(Entity).filter(Entity.identifier == self.identifier).first()
            if not entity:
                raise ValidationException("Entity not found")

            if entity.embedded_description is None:
                raise ValidationException("Entity has no embedding")

            similarity = 1 - Entity.embedded_description.cosine_distance(entity.embedded_description)

            query = (
                select(Entity, similarity.label("similarity"))
                .where(similarity > self.similarity_threshold)
                .where(Entity.embedded_description.isnot(None))
                .where(Entity.identifier != entity.identifier)
            )

            if self.filter_community and entity.leiden_community is not None:
                query = query.where(Entity.leiden_community == entity.leiden_community)

            query = query.order_by(similarity.desc()).limit(self.max_results)

            return [
                {"entity": row.Entity.to_dict(), "similarity": float(row.similarity)} for row in session.execute(query)
            ]
