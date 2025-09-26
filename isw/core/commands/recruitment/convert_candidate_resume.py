from ....shared.logging.logger import logger
from ...errors import ProcessingException
from ...schemas.base import id_schema
from ...services.ats import ATSService
from ...services.ocr import OCRService
from ...utils.helpers import safe_get
from ..base import WriteCommand


class ConvertCandidateResumeCommand(WriteCommand):
    def __init__(self, id: str):
        self.id = id

    def validate(self):
        id_schema.load(self.__dict__)

    def execute(self) -> str | None:
        """Pull PDF from Ashby and convert to raw text"""
        try:
            ats = ATSService()

            candidate = ats.get_candidate(self.id)
            resume = ats.get_file_info(safe_get(candidate, "resumeFileHandle", "handle"))
            text = OCRService().extract_text(safe_get(resume, "url"))

            return "\n\n".join([page.markdown for page in text])

        except Exception as e:
            logger.error(f"Candidate resume not converted for candidate ID: {self.id} - {e}")
            raise ProcessingException("Candidate resume not converted") from e
