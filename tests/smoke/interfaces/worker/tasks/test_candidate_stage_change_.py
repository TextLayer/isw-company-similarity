from unittest.mock import patch

import pytest

from tests import BaseTest
from isw.interfaces.worker.tasks import task_registry


class TestSmokeCandidateStageChange(BaseTest):
    @pytest.mark.smoke
    @patch("textlayer.core.services.ats.ashby.AshbyService.get_application")
    @patch("textlayer.core.services.ats.ashby.AshbyService.get_candidate")
    @patch("textlayer.core.commands.recruitment.candidate_stage_change.SearchService.search")
    @patch("textlayer.core.commands.recruitment.candidate_stage_change.ATSService.add_note_to_candidate")
    def test_candidate_stage_change(
        self,
        mock_add_note,
        mock_search,
        mock_get_candidate,
        mock_get_application,
        mock_ashby_application_data,
        mock_ashby_candidate_data,
        test_application_id,
        test_candidate_id,
    ):
        mock_get_application.return_value = mock_ashby_application_data
        mock_get_candidate.return_value = mock_ashby_candidate_data

        mock_search.return_value.hits = [{"_source": {"candidate_id": test_candidate_id}}]
        mock_search.return_value.total = 1

        mock_add_note.return_value = True

        task_registry.defer(
            "candidate_stage_change",
            {
                "application_id": test_application_id,
                "candidate_id": test_candidate_id,
            },
        ).get()
