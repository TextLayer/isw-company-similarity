from isw.core.commands.base import ReadCommand
from isw.core.errors import NotFoundException
from isw.core.schemas.base import id_schema
from isw.core.services.ats import ATSService


class GetCandidateDetailsCommand(ReadCommand):
    def __init__(self, id: str):
        self.id = id

    def validate(self):
        id_schema.load(self.__dict__)

    def execute(self) -> dict:
        response = ATSService().get_candidate(self.id)
        if response is None:
            raise NotFoundException("Candidate not found")

        return response
