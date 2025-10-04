from ...commands.base import ReadCommand
from ...errors.validation import ValidationException
from ...models.company_models import Company
from ...services.database.service import DatabaseService


class GetCompanyCommand(ReadCommand):
    def __init__(self, cik: str):
        self.cik = cik

    def validate(self):
        if not self.cik:
            raise ValidationException("CIK is required")

    def execute(self):
        with DatabaseService.get_instance().session_scope() as session:
            company = session.query(Company).filter(Company.cik == self.cik).first()
            return company.to_dict() if company else None
