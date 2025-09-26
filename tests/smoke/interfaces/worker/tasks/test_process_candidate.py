from unittest.mock import patch

import pytest

from tests import BaseTest
from isw.interfaces.worker.tasks import task_registry


class TestProcessCandidate(BaseTest):
    @pytest.mark.smoke
    @patch("textlayer.interfaces.worker.tasks.process_candidate.RecruitmentController.update_candidate_notes")
    @patch("textlayer.interfaces.worker.tasks.process_candidate.RecruitmentController.create_candidate")
    @patch("textlayer.core.services.ats.ashby.AshbyService.get_application")
    @patch("textlayer.core.commands.recruitment.get_job_details.SearchService.get_document")
    def test_resume_parsing_and_grading_pipeline(
        self,
        mock_get_document,
        mock_get_application,
        mock_create_candidate,
        mock_update_candidate_notes,
        mock_ashby_application_data,
        mock_job_document_data,
        test_application_id,
        test_candidate_id,
    ):
        """
        This is a quazi-end-to-end test of the resume parsing and grading pipeline.
        It only cares about making it to the bottom of the pipeline and generally asserting its result.
        I've mocked both ATSService().update_candidate_notes() and SearchService().create_document()
        to make it a bit more idempotent against 3rd party integrations.
        """
        mock_get_application.return_value = mock_ashby_application_data
        mock_get_document.return_value = mock_job_document_data

        result = task_registry.defer(
            "process_candidate",
            {
                "application_id": test_application_id,
                "candidate_id": test_candidate_id,
            },
        ).get()

        # NOTE: our test candidate has nothing to do with the paired job description
        assert result == "Not recommended"

        document_data = mock_create_candidate.call_args.kwargs
        assert document_data["current_interview_stage"] == "Technical/Project Round"
        assert document_data["full_name"] == "Vibhu Bhalla"
        assert document_data["resume_text"].startswith("# VIBHU BHALLA ")
        assert mock_create_candidate.call_count == 1
        assert mock_update_candidate_notes.call_count == 1
