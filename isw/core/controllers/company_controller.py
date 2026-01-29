from isw.core.commands.company.get_companies import GetCompaniesCommand
from isw.core.commands.company.get_company import GetCompanyCommand

from ..commands.company.get_similar_companies import GetSimilarCompaniesCommand
from .base import Controller


class CompanyController(Controller):
    def get_similar_companies(self, **kwargs):
        command = GetSimilarCompaniesCommand(**kwargs)
        return self.executor.execute_read(command)

    def get_companies(self, **kwargs):
        command = GetCompaniesCommand(**kwargs)
        return self.executor.execute_read(command)

    def get_company_by_cik(self, **kwargs):
        command = GetCompanyCommand(**kwargs)
        return self.executor.execute_read(command)
