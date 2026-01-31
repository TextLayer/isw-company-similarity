from abc import ABC, abstractmethod
from dataclasses import dataclass


class EntityIdentifier(ABC):
    """
    Base class for entity identifiers with normalized value comparison.

    Subclasses must implement value normalization (e.g., zero-padding for CIK,
    uppercase for LEI) so that equivalent identifiers compare equal regardless
    of their raw input format.
    """

    @property
    @abstractmethod
    def value(self) -> str:
        """Normalized identifier value used for comparison and storage."""
        ...

    @classmethod
    @abstractmethod
    def is_valid(cls, value: str) -> bool: ...

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.value!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, EntityIdentifier):
            return NotImplemented
        return type(self) is type(other) and self.value == other.value

    def __hash__(self) -> int:
        return hash((type(self), self.value))


@dataclass(frozen=True, eq=False)
class CIK(EntityIdentifier):
    """
    SEC Central Index Key - numeric identifier up to 10 digits.

    Normalizes to 10-digit zero-padded format for consistent comparison:
    CIK("320193") == CIK("0000320193")
    """

    _raw_value: str

    def __post_init__(self) -> None:
        if not self.is_valid(self._raw_value):
            raise ValueError(f"Invalid CIK: {self._raw_value}")

    @property
    def value(self) -> str:
        return self._raw_value.lstrip("0").zfill(10)

    @classmethod
    def is_valid(cls, value: str) -> bool:
        if not value:
            return False
        stripped = value.lstrip("0")
        if not stripped:
            return True
        return stripped.isdigit() and len(stripped) <= 10


@dataclass(frozen=True, eq=False)
class LEI(EntityIdentifier):
    """
    Legal Entity Identifier - exactly 20 alphanumeric characters.

    Normalizes to uppercase for consistent comparison.
    """

    _raw_value: str

    def __post_init__(self) -> None:
        if not self.is_valid(self._raw_value):
            raise ValueError(f"Invalid LEI: {self._raw_value}")

    @property
    def value(self) -> str:
        return self._raw_value.upper()

    @classmethod
    def is_valid(cls, value: str) -> bool:
        return len(value) == 20 and value.isalnum()


def parse_identifier(value: str) -> EntityIdentifier:
    """Parse a string into the appropriate identifier type."""
    if CIK.is_valid(value):
        return CIK(value)
    if LEI.is_valid(value):
        return LEI(value)
    raise ValueError(f"Unknown identifier format: {value}")


def is_cik(value: str) -> bool:
    return CIK.is_valid(value)


def is_lei(value: str) -> bool:
    return LEI.is_valid(value)
