import time
from functools import cached_property

from ....shared.config import config
from ....shared.logging.logger import logger
from ...errors.validation import ValidationException
from ...schemas.recruitment_schemas import candidate_metadata_schema
from ...services.ats import ATSService
from ...services.doppler import DopplerService
from ...services.jwt import JWTService
from ...services.mail.service import MailService
from ...services.mail.types import EmailRecipients
from ...services.notion import NotionService
from ...services.search.service import SearchService
from ...services.search.types import SearchQuery
from ...services.storage import StorageService
from ...utils.helpers import safe_get
from ...utils.recruitment.constants import JOB_TEMPLATES, DateTimeConstants
from ..base import WriteCommand


class CandidateStageChangeCommand(WriteCommand):
    def __init__(self, application_id: str, candidate_id: str):
        self.application_id = application_id
        self.candidate_id = candidate_id
        self.conf = config()

    @cached_property
    def ats_service(self):
        return ATSService()

    @cached_property
    def search_service(self):
        return SearchService()

    def execute(self) -> bool:
        self._update_candidate_stage()
        application = self.ats_service.get_application(self.application_id)

        if safe_get(application, "currentInterviewStage", "title") == "Technical/Project Round":
            self._send_technical_interview_assignment(
                job_id=safe_get(application, "job", "id"),
            )

        return True

    def validate(self):
        candidate_metadata_schema.load(
            {
                "application_id": self.application_id,
                "candidate_id": self.candidate_id,
            }
        )

        if not self._get_existing_candidate():
            raise ValidationException("Candidate does not exist")

    def _get_existing_candidate(self):
        query = {
            "bool": {
                "must": [
                    {"match": {"application_id": self.application_id}},
                    {"match": {"candidate_id": self.candidate_id}},
                ]
            }
        }

        results = self.search_service.search(
            index=self.conf.recruitment_candidate_index,
            query=SearchQuery(query=query, size=1),
        )

        return results.hits[0] if (results.total or 0) > 0 else None

    def _update_candidate_stage(self):
        application = self.ats_service.get_application(self.application_id) or {}

        query = {
            "bool": {
                "must": [
                    {"match": {"application_id": self.application_id}},
                    {"match": {"candidate_id": self.candidate_id}},
                ]
            }
        }

        update_script = {
            "source": "ctx._source.current_interview_stage = params.new_stage",
            "params": {"new_stage": application.get("currentInterviewStage")},
        }

        self.search_service.provider.update_by_query(
            index=self.conf.recruitment_candidate_index,
            query=SearchQuery(query=query),
            update=update_script,
        )

    def _send_technical_interview_assignment(self, job_id: str):
        try:
            candidate = self.ats_service.get_candidate(self.candidate_id) or {}
            candidate_email = (candidate.get("primaryEmailAddress") or {}).get("value")
            candidate_name = candidate.get("name", "Candidate")

            if not candidate_email:
                logger.error(f"No email address found for candidate: {self.candidate_id}")
                return

            assignment_data = self._prepare_assignment_data(candidate_name)

            sent = self._send_assignment_email(candidate_email, assignment_data, job_id, candidate_name)
            if not sent:
                logger.error(f"Failed to send technical interview assignment to: {candidate_email}")
                return

            self._create_assignment_note(candidate_email, assignment_data["expire_at"])

            logger.info(f"Successfully sent technical interview assignment to: {candidate_email}")
        except Exception as e:
            logger.error(f"Failed to send technical interview assignment: {str(e)}")
            raise

    def _prepare_assignment_data(self, candidate_name: str) -> dict:
        logger.info(f"Preparing assignment content for candidate: {self.candidate_id}")

        presigned_url = StorageService("aws_s3", bucket_name=self.conf.assignment_s3_bucket).get_download_url(
            key=self.conf.assignment_s3_key, expires_in=DateTimeConstants.SEVEN_DAYS
        )

        notion_content = NotionService(api_token=self.conf.notion_api_token).retrieve_page_markdown_html(
            self.conf.notion_engineer_assignment_id,
        )

        in_two_weeks = int(time.time()) + DateTimeConstants.TWO_WEEKS
        doppler_token = self._create_doppler_token(candidate_name, in_two_weeks)

        return {
            "notion_content": notion_content,
            "presigned_url": presigned_url,
            "doppler_token": doppler_token,
            "expire_at": in_two_weeks,
        }

    def _create_doppler_token(self, candidate_name: str, expire_at: int) -> str:
        """Create a Doppler service token for the candidate."""
        token_name = f"candidate-{candidate_name.replace(' ', '-').lower()}-{self.candidate_id[:8]}"
        doppler_response = DopplerService(api_token=self.conf.doppler_api_token).create_service_token(
            project=self.conf.doppler_project,
            config=self.conf.doppler_config,
            name=token_name,
            expire_at=expire_at,
            access="read",
        )

        return doppler_response.get("token", {}).get("key", "")

    def _send_assignment_email(
        self,
        candidate_email: str,
        assignment_data: dict,
        job_id: str,
        candidate_name: str,
    ) -> bool:
        """Send the technical interview assignment email."""
        job_template = self._get_job_template(job_id)
        if not job_template:
            return False

        template_name_key = job_template.get("template_name")
        subject = job_template.get("subject")

        token = JWTService().generate_token(
            subject=self.candidate_id,
            data={
                "candidate_id": self.candidate_id,
                "application_id": self.application_id,
                "candidate_name": candidate_name,
            },
            expires_in=DateTimeConstants.TWO_WEEKS,
        )

        submission_url = f"{self.conf.client_url}/recruitment/submission?token={token}"

        if template_name_key == "technical_interview":
            template_data = {
                "s3_url": assignment_data["presigned_url"],
                "doppler_token": assignment_data["doppler_token"],
                "body": assignment_data["notion_content"].get("html"),
                "body_text": assignment_data["notion_content"].get("markdown"),
                "submission_url": submission_url,
            }
        else:
            template_data = {
                "candidate_first_name": candidate_name,
            }

        return MailService().send_email(
            recipients=EmailRecipients(to=[candidate_email]),
            subject=subject,
            template_name=f"interviews/{template_name_key}",
            template_data=template_data,
        )

    def _create_assignment_note(self, candidate_email: str, expire_at: int):
        expiry_date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(expire_at))
        note_content = (
            f"<p>Technical interview assignment sent to {candidate_email}</p><p>Assignment expires: {expiry_date}</p>"
        )
        self.ats_service.add_note_to_candidate(candidate_id=self.candidate_id, note=note_content, notify=False)

    def _get_job_template(self, job_id: str) -> dict:
        """Map job id to email template and subject."""
        for job in JOB_TEMPLATES:
            if job.get("id") == job_id:
                return {
                    "template_name": job.get("template_name"),
                    "subject": job.get("subject"),
                }

        return {}
