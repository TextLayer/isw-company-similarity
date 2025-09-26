from ...errors import ProcessingException
from ...schemas.recruitment_schemas import candidate_note_schema
from ...services.ats import ATSService
from ..base import WriteCommand


class UpdateCandidateNotesCommand(WriteCommand):
    def __init__(self, candidate_id: str, note: str):
        self.candidate_id = candidate_id
        self.note = note

    def validate(self):
        candidate_note_schema.load(self.__dict__)

    def execute(self):
        if not ATSService().add_note_to_candidate(self.candidate_id, self.note):
            raise ProcessingException("Failed to update candidate notes")
