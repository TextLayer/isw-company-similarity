from datetime import datetime

from sqlalchemy import Column, DateTime

from isw.core.services.database import Base


class BaseModel(Base):
    __abstract__ = True
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        right_now = datetime.now()

        if "created_at" not in kwargs:
            self.created_at = right_now
        if "updated_at" not in kwargs:
            self.updated_at = right_now

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.id}>"