from ..commands.recruitment.analyze_candidate_resume import AnalyzeCandidateResumeCommand
from ..commands.recruitment.candidate_stage_change import CandidateStageChangeCommand
from ..commands.recruitment.cleanup_technical_submission import CleanupTechnicalSubmissionCommand
from ..commands.recruitment.convert_candidate_resume import ConvertCandidateResumeCommand
from ..commands.recruitment.create_candidate import CreateCandidateCommand
from ..commands.recruitment.create_job import CreateJobCommand
from ..commands.recruitment.create_jobs_index import CreateJobsIndexCommand
from ..commands.recruitment.download_technical_submission import DownloadTechnicalSubmissionCommand
from ..commands.recruitment.generate_technical_submission_request import GenerateTechnicalSubmissionRequestCommand
from ..commands.recruitment.get_application_details import GetApplicationDetails
from ..commands.recruitment.get_candidate_details import GetCandidateDetailsCommand
from ..commands.recruitment.get_job_details import GetJobDetailsCommand
from ..commands.recruitment.remove_job import RemoveJobCommand
from ..commands.recruitment.search_jobs import SearchJobsCommand
from ..commands.recruitment.update_candidate_notes import UpdateCandidateNotesCommand
from ..commands.recruitment.update_job import UpdateJobCommand
from ..commands.recruitment.upload_technical_submission import UploadTechnicalSubmissionCommand
from .base import Controller


class RecruitmentController(Controller):
    def analyze_candidate_resume(self, **kwargs):
        return self.executor.execute_read(AnalyzeCandidateResumeCommand(**kwargs))

    def cleanup_technical_submission(self, **kwargs):
        return self.executor.execute_write(CleanupTechnicalSubmissionCommand(**kwargs))

    def convert_candidate_resume(self, **kwargs):
        return self.executor.execute_write(ConvertCandidateResumeCommand(**kwargs))

    def create_candidate(self, **kwargs):
        return self.executor.execute_write(CreateCandidateCommand(**kwargs))

    def create_job(self, **kwargs):
        return self.executor.execute_write(CreateJobCommand(**kwargs))

    def create_jobs_index(self, **kwargs):
        return self.executor.execute_write(CreateJobsIndexCommand(**kwargs))

    def download_technical_submission(self, **kwargs):
        return self.executor.execute_write(DownloadTechnicalSubmissionCommand(**kwargs))

    def generate_technical_submission_request(self, **kwargs):
        return self.executor.execute_write(GenerateTechnicalSubmissionRequestCommand(**kwargs))

    def get_application_details(self, **kwargs):
        return self.executor.execute_read(GetApplicationDetails(**kwargs))

    def get_candidate_details(self, **kwargs):
        return self.executor.execute_read(GetCandidateDetailsCommand(**kwargs))

    def get_job_details(self, **kwargs):
        return self.executor.execute_read(GetJobDetailsCommand(**kwargs))

    def remove_job(self, **kwargs):
        return self.executor.execute_write(RemoveJobCommand(**kwargs))

    def search_jobs(self, **kwargs):
        return self.executor.execute_read(SearchJobsCommand(**kwargs))

    def update_candidate_notes(self, **kwargs):
        return self.executor.execute_write(UpdateCandidateNotesCommand(**kwargs))

    def update_job(self, **kwargs):
        return self.executor.execute_write(UpdateJobCommand(**kwargs))

    def upload_technical_submission(self, **kwargs):
        return self.executor.execute_write(UploadTechnicalSubmissionCommand(**kwargs))

    def candidate_stage_change(self, **kwargs):
        return self.executor.execute_write(CandidateStageChangeCommand(**kwargs))
