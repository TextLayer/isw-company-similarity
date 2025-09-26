from ...errors import NotFoundException
from ...schemas.base import id_schema
from ...services.ats import ATSService
from ..base import ReadCommand


class GetApplicationDetails(ReadCommand):
    def __init__(self, id: str):
        self.id = id

    def validate(self):
        id_schema.load(self.__dict__)

    def execute(self) -> dict:
        response = ATSService().get_application(self.id)
        if response is None:
            raise NotFoundException("Application not found")

        return response
