from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

__all__ = [
    "Base",
    "relationship",
]
