from ...commands.base import ReadCommand
from ...errors.validation import ValidationException
from ...models.company_models import Company
from ...services.database.service import DatabaseService


class GetCompanyCommand(ReadCommand):
    def __init__(self, identifier: str):
        self.identifier = identifier

    def validate(self):
        if not self.identifier:
            raise ValidationException("Identifier is required")

    def execute(self):
        with DatabaseService.get_instance().session_scope() as session:
            company = session.query(Company).filter(Company.identifier == self.identifier).first()
            return company.to_dict() if company else None
