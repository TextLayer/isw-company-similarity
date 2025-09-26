import pytest

from tests import BaseTest
from isw.core.services.ats import ATSService


class TestATSServiceIntegration(BaseTest):
    @pytest.mark.integration
    def test_get_candidate_not_found(self):
        ats_service = ATSService()
        id = "e306a48a-b895-4292-baff-666949f51a11"
        candidate = ats_service.get_candidate(id)
        assert candidate is None

    @pytest.mark.integration
    def test_get_candidate_found(self):
        ats_service = ATSService()
        id = "e306a48a-b895-4292-baff-666949f51a28"
        candidate = ats_service.get_candidate(id)
        assert candidate.get("id") == id
