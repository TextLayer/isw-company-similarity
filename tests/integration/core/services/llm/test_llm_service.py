import json
import os
import unittest

import pytest
from pydantic import BaseModel

from isw.core.services.llm import LLMService
from tests.conftest import get_fixture_path

SEC_FIXTURES = get_fixture_path("data_sources", "sec_data")
XBRL_FIXTURES = get_fixture_path("data_sources", "xbrl_json")


def load_apple_business_description() -> str:
    """Load Apple's extracted business description from fixture."""
    with open(SEC_FIXTURES / "apple_10k_item1_business.json") as f:
        data = json.load(f)
    return data["item1_business_text"]


def load_kainos_business_description() -> str:
    """Load Kainos' business description from XBRL fixture."""
    with open(XBRL_FIXTURES / "kainos_2022.json") as f:
        data = json.load(f)
    return data["facts"]["fact-1"]["value"]


class ExtractedCompanyInfo(BaseModel):
    company_name: str
    industry: str
    primary_products_or_services: list[str]
    is_technology_company: bool


class ExtractedBusinessSummary(BaseModel):
    summary: str
    key_business_segments: list[str]
    geographic_regions: list[str]


@pytest.mark.skipif(
    os.environ.get("OPENAI_API_KEY") is None or os.environ.get("OPENAI_API_KEY") == "",
    reason="OPENAI_API_KEY not set. Set it to run LLM integration tests.",
)
class TestLLMServiceWithFixtures(unittest.TestCase):
    """Integration tests using real fixture data."""

    @classmethod
    def setUpClass(cls):
        try:
            cls.service = LLMService(model="gpt-4o-mini")
            cls.apple_description = load_apple_business_description()[:8000]
            cls.kainos_description = load_kainos_business_description()
        except Exception as e:
            pytest.skip(f"Failed to initialize: {e}")

    def test_extracts_company_info_from_apple_10k(self):
        """LLM should extract structured company info from Apple's 10-K."""
        result = self.service.structured_output(
            messages=[
                {
                    "role": "system",
                    "content": "Extract company information from SEC filing text.",
                },
                {
                    "role": "user",
                    "content": f"Extract company information:\n\n{self.apple_description}",
                },
            ],
            output_structure=ExtractedCompanyInfo,
        )

        assert isinstance(result, ExtractedCompanyInfo)
        assert "apple" in result.company_name.lower()
        assert result.is_technology_company is True
        assert len(result.primary_products_or_services) > 0
        # Apple sells iPhones, Macs, etc.
        products_lower = [p.lower() for p in result.primary_products_or_services]
        assert any("iphone" in p or "mac" in p or "phone" in p for p in products_lower)

    def test_extracts_business_summary_from_apple_10k(self):
        """LLM should summarize Apple's business from 10-K text."""
        result = self.service.structured_output(
            messages=[
                {
                    "role": "system",
                    "content": "Summarize the business description from this SEC filing.",
                },
                {
                    "role": "user",
                    "content": f"Summarize this business:\n\n{self.apple_description}",
                },
            ],
            output_structure=ExtractedBusinessSummary,
        )

        assert isinstance(result, ExtractedBusinessSummary)
        assert len(result.summary) > 100
        assert len(result.key_business_segments) > 0

    def test_extracts_company_info_from_kainos_xbrl(self):
        """LLM should extract structured company info from Kainos XBRL data."""
        # Note: Kainos fixture text doesn't contain the company name explicitly
        # (written in first person: "Our Digital Services division...")
        # So we test that extraction works and correctly identifies key attributes
        result = self.service.structured_output(
            messages=[
                {
                    "role": "system",
                    "content": "Extract company information from this business description. "
                    "The company is Kainos Group plc.",
                },
                {
                    "role": "user",
                    "content": f"Extract company information:\n\n{self.kainos_description}",
                },
            ],
            output_structure=ExtractedCompanyInfo,
        )

        assert isinstance(result, ExtractedCompanyInfo)
        assert result.is_technology_company is True
        assert len(result.primary_products_or_services) > 0
        # Should identify Workday-related services
        services_lower = " ".join(result.primary_products_or_services).lower()
        assert "workday" in services_lower or "digital" in services_lower

    def test_different_output_structures_same_input(self):
        """Same input text should work with different Pydantic output structures."""
        # First get company info
        company_info = self.service.structured_output(
            messages=[{"role": "user", "content": f"Extract:\n\n{self.apple_description}"}],
            output_structure=ExtractedCompanyInfo,
        )

        # Then get business summary
        business_summary = self.service.structured_output(
            messages=[{"role": "user", "content": f"Summarize:\n\n{self.apple_description}"}],
            output_structure=ExtractedBusinessSummary,
        )

        # Both should succeed with different structures
        assert isinstance(company_info, ExtractedCompanyInfo)
        assert isinstance(business_summary, ExtractedBusinessSummary)
        assert company_info.company_name != ""
        assert business_summary.summary != ""
