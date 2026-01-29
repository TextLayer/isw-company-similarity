import json
import os
import unittest

import pytest

from isw.core.services.data_sources.edgar_data_source import SECEdgarDataSource
from isw.core.services.data_sources.parsers import parse_10k_business_section
from tests.conftest import get_fixture_path

SEC_FIXTURES = get_fixture_path("data_sources", "sec_data")


class TestBusinessDescriptionFromHTML(unittest.TestCase):
    """Tests using Apple 10-K HTML filing."""

    @classmethod
    def setUpClass(cls):
        html_path = SEC_FIXTURES / "apple_10k_2025.htm"
        if not html_path.exists():
            raise unittest.SkipTest("SEC HTML fixture not downloaded")

        with open(html_path) as f:
            cls.apple_html = f.read()

    def test_extracts_business_description_from_10k(self):
        result = parse_10k_business_section(self.apple_html)

        assert result is not None
        assert len(result) > 500

    def test_extracted_text_contains_company_description(self):
        result = parse_10k_business_section(self.apple_html)

        assert result is not None
        assert "designs, manufactures and markets" in result
        assert "smartphones" in result

    def test_extracted_text_contains_product_info(self):
        result = parse_10k_business_section(self.apple_html)

        assert result is not None
        assert "iPhone" in result
        assert "Mac" in result
        assert "iPad" in result

    def test_extracted_text_contains_services_info(self):
        result = parse_10k_business_section(self.apple_html)

        assert result is not None
        assert "Services" in result
        assert "App Store" in result

    def test_extracted_text_does_not_contain_risk_factors(self):
        result = parse_10k_business_section(self.apple_html)

        assert result is not None
        assert "The Company's operations and performance depend significantly on global" not in result

    def test_extracted_text_does_not_contain_toc(self):
        result = parse_10k_business_section(self.apple_html)

        assert result is not None
        assert "TABLE OF CONTENTS" not in result


class TestRevenueFromCompanyFacts(unittest.TestCase):
    """Tests using Apple company facts JSON."""

    @classmethod
    def setUpClass(cls):
        facts_path = SEC_FIXTURES / "apple_company_facts.json"
        if not facts_path.exists():
            raise unittest.SkipTest("Company facts fixture not downloaded")

        with open(facts_path) as f:
            cls.company_facts = json.load(f)

        cls.source = SECEdgarDataSource(user_agent="Test test@example.com")

    def test_extracts_revenue_from_company_facts(self):
        result = self.source._extract_revenue_from_facts(self.company_facts)

        assert result is not None
        assert result.currency == "USD"

    def test_revenue_is_reasonable_value(self):
        result = self.source._extract_revenue_from_facts(self.company_facts)

        assert result is not None
        # Apple's revenue should be in the hundreds of billions
        assert result.amount > 200_000_000_000  # > $200B

    def test_revenue_has_valid_period_end(self):
        result = self.source._extract_revenue_from_facts(self.company_facts)

        assert result is not None
        assert result.period_end >= "2023-01-01"

    def test_revenue_has_valid_source_tag(self):
        result = self.source._extract_revenue_from_facts(self.company_facts)

        assert result is not None
        assert result.source_tag.startswith("us-gaap:")


class TestExpectedBusinessDescriptionContent(unittest.TestCase):
    """Tests that verify extracted content matches expected fixture content."""

    @classmethod
    def setUpClass(cls):
        item1_path = SEC_FIXTURES / "apple_10k_item1_business.json"
        if not item1_path.exists():
            raise unittest.SkipTest("Item 1 fixture not available")

        with open(item1_path) as f:
            cls.expected_data = json.load(f)

        html_path = SEC_FIXTURES / "apple_10k_2025.htm"
        with open(html_path) as f:
            cls.apple_html = f.read()

    def test_extracted_text_matches_expected_content(self):
        result = parse_10k_business_section(self.apple_html)

        assert result is not None
        assert "Company Background" in result
        assert "designs, manufactures and markets smartphones" in result

        expected_text = self.expected_data["item1_business_text"]
        assert abs(len(result) - len(expected_text)) < 1000

    def test_key_phrases_are_present(self):
        result = parse_10k_business_section(self.apple_html)

        key_phrases = [
            "fiscal year",
            "iPhone",
            "Mac",
            "iPad",
            "Services",
            "App Store",
            "AppleCare",
            "segments",
            "Americas",
            "Europe",
            "Greater China",
        ]

        for phrase in key_phrases:
            assert phrase in result, f"Expected phrase '{phrase}' not found in extracted text"


@pytest.mark.skipif(
    os.environ.get("RUN_LIVE_API_TESTS") != "1",
    reason="Live API tests disabled. Set RUN_LIVE_API_TESTS=1 to run.",
)
class TestLiveAPI(unittest.TestCase):
    """Live API tests for SEC EDGAR data source."""

    def setUp(self):
        self.source = SECEdgarDataSource(
            user_agent="ISW Test admin@example.com",
            timeout=60.0,
        )
        self.apple_cik = "0000320193"

    def test_fetches_apple_filings(self):
        filings = self.source.list_filings(self.apple_cik, limit=5)

        assert len(filings) > 0
        assert filings[0].identifier == self.apple_cik

    def test_fetches_apple_10k(self):
        filing = self.source.get_latest_annual_filing(self.apple_cik)

        assert filing is not None
        assert filing.filing_type == "10-K"
        assert filing.document_url is not None

    def test_fetches_apple_business_description(self):
        description = self.source.get_business_description(self.apple_cik)

        assert description is not None
        assert len(description.text) > 500
        assert "designs, manufactures" in description.text
        assert description.source_filing_type == "10-K"
        assert description.extraction_method == "html_parse"

    def test_fetches_apple_revenue(self):
        revenue = self.source.get_revenue(self.apple_cik)

        assert revenue is not None
        assert revenue.currency == "USD"
        assert revenue.amount > 200_000_000_000
