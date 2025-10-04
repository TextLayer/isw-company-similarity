from ...commands.base import ReadCommand
from ...errors.validation import ValidationException
from ...models.company_models import CompanyFacts
from ...services.database.service import DatabaseService


class GetCompanyReportsCommand(ReadCommand):
    def __init__(self, cik: str, fiscal_year: str = None, filing_period: str = None, form_type: str = None):
        self.cik = cik
        self.fiscal_year = fiscal_year
        self.filing_period = filing_period
        self.form_type = form_type

    def validate(self):
        if not self.cik:
            raise ValidationException("CIK is required")
        return True

    def execute(self):
        with DatabaseService.get_instance().session_scope() as session:
            query = session.query(CompanyFacts).filter(CompanyFacts.cik == int(self.cik))
            
            if self.fiscal_year:
                query = query.filter(CompanyFacts.fiscal_year == self.fiscal_year)
            if self.filing_period:
                query = query.filter(CompanyFacts.filing_period == self.filing_period)
            if self.form_type:
                query = query.filter(CompanyFacts.form_type == self.form_type)

            company_facts = query.all()
            return [company_fact.to_dict() for company_fact in company_facts]