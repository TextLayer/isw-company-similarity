import math

from ...commands.base import ReadCommand
from ...errors.validation import ValidationException
from ...models.company_models import Company
from ...services.database.service import DatabaseService


class GetCompaniesCommand(ReadCommand):
    def __init__(self, page: int = 1, page_size: int = 10):
        self.page = page
        self.page_size = page_size

    def validate(self):
        if self.page < 1:
            raise ValidationException("Page must be greater than 0")
        if self.page_size < 1:
            raise ValidationException("Page size must be greater than 0")
        return True

    def execute(self):
        with DatabaseService.get_instance().session_scope() as session:
            total_count = session.query(Company).count()
            total_pages = math.ceil(total_count / self.page_size)
            if self.page > total_pages:
                raise ValidationException("Page out of range")

            companies = session.query(Company).offset((self.page - 1) * self.page_size).limit(self.page_size).all()
            
            return {
                "companies": [company.to_dict() for company in companies],
                "total_pages": total_pages,
                "total_count": total_count,
                "page": self.page,
                "page_size": self.page_size,
                "has_next": self.page < total_pages,
                "has_previous": self.page > 1,
                "next_page": self.page + 1,
                "previous_page": self.page - 1
            }