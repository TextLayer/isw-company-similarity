from abc import ABC, abstractmethod

from isw.core.services.entities.models import EntityRecord


class EntityRegistry(ABC):
    """
    Abstract base for entity discovery registries.

    Implementations discover entities from regulatory filing databases
    (SEC EDGAR for US, filings.xbrl.org for ESEF).
    """

    @abstractmethod
    def fetch_entities(self) -> list[EntityRecord]: ...

    @abstractmethod
    def get_source_name(self) -> str: ...
