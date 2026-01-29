"""Integration tests for SEC EDGAR data source.

Tests using real SEC filing data to verify extraction works correctly.
Fixtures are downloaded from actual SEC EDGAR filings.
"""

import json
import os
import unittest
from pathlib import Path

import pytest

from isw.core.services.data_sources.edgar_data_source import SECEdgarDataSource
from isw.core.services.data_sources.parsers import extract_item1_business

REAL_SEC_FIXTURES = Path(__file__).parent.parent.parent.parent.parent / "fixtures" / "data_sources" / "real_sec_data"


class TestBusinessDescriptionFromRealHTML(unittest.TestCase):
    """Tests using real Apple 10-K HTML filing."""

    @classmethod
    def setUpClass(cls):
        """Load real SEC HTML fixture."""
        html_path = REAL_SEC_FIXTURES / "apple_10k_2025.htm"
        if not html_path.exists():
            raise unittest.SkipTest("Real SEC HTML fixture not downloaded")

        with open(html_path) as f:
            cls.apple_html = f.read()

    def test_extracts_business_description_from_real_10k(self):
        """Should extract business description from real Apple 10-K HTML."""
        result = extract_item1_business(self.apple_html)

        assert result is not None
        assert len(result) > 5000  # Item 1 should be substantial

    def test_extracted_text_contains_company_description(self):
        """Extracted text should contain Apple's company description."""
        result = extract_item1_business(self.apple_html)

        assert result is not None
        assert "designs, manufactures and markets" in result
        assert "smartphones" in result

    def test_extracted_text_contains_product_info(self):
        """Extracted text should contain product information."""
        result = extract_item1_business(self.apple_html)

        assert result is not None
        assert "iPhone" in result
        assert "Mac" in result
        assert "iPad" in result

    def test_extracted_text_contains_services_info(self):
        """Extracted text should contain services information."""
        result = extract_item1_business(self.apple_html)

        assert result is not None
        assert "Services" in result
        assert "App Store" in result

    def test_extracted_text_does_not_contain_risk_factors(self):
        """Extracted text should not bleed into Risk Factors section."""
        result = extract_item1_business(self.apple_html)

        assert result is not None
        # Risk Factors section should not be included
        assert "The Company's operations and performance depend significantly on global" not in result

    def test_extracted_text_does_not_contain_toc(self):
        """Extracted text should not include table of contents."""
        result = extract_item1_business(self.apple_html)

        assert result is not None
        # TOC items typically have page numbers like "5", "17", etc.
        assert "TABLE OF CONTENTS" not in result


class TestRevenueFromRealCompanyFacts(unittest.TestCase):
    """Tests using real Apple company facts JSON."""

    @classmethod
    def setUpClass(cls):
        """Load real company facts fixture."""
        facts_path = REAL_SEC_FIXTURES / "apple_company_facts.json"
        if not facts_path.exists():
            raise unittest.SkipTest("Real company facts fixture not downloaded")

        with open(facts_path) as f:
            cls.company_facts = json.load(f)

        cls.source = SECEdgarDataSource(user_agent="Test test@example.com")

    def test_extracts_revenue_from_real_company_facts(self):
        """Should extract revenue from real Apple company facts."""
        result = self.source._extract_revenue_from_facts(self.company_facts)

        assert result is not None
        assert result.currency == "USD"

    def test_revenue_is_reasonable_value(self):
        """Extracted revenue should be a reasonable value for Apple."""
        result = self.source._extract_revenue_from_facts(self.company_facts)

        assert result is not None
        # Apple's revenue should be in the hundreds of billions
        assert result.amount > 300_000_000_000  # > $300B
        assert result.amount < 600_000_000_000  # < $600B

    def test_revenue_has_valid_period_end(self):
        """Revenue should have a valid fiscal year end date."""
        result = self.source._extract_revenue_from_facts(self.company_facts)

        assert result is not None
        assert result.period_end >= "2023-01-01"

    def test_revenue_has_valid_source_tag(self):
        """Revenue should have a valid US-GAAP source tag."""
        result = self.source._extract_revenue_from_facts(self.company_facts)

        assert result is not None
        assert result.source_tag.startswith("us-gaap:")


class TestExpectedBusinessDescriptionContent(unittest.TestCase):
    """Tests that verify extracted content matches expected fixture content."""

    @classmethod
    def setUpClass(cls):
        """Load expected Item 1 content fixture."""
        item1_path = REAL_SEC_FIXTURES / "apple_10k_item1_business.json"
        if not item1_path.exists():
            raise unittest.SkipTest("Item 1 fixture not available")

        with open(item1_path) as f:
            cls.expected_data = json.load(f)

        html_path = REAL_SEC_FIXTURES / "apple_10k_2025.htm"
        with open(html_path) as f:
            cls.apple_html = f.read()

    def test_extracted_text_matches_expected_content(self):
        """Extracted text should match the expected fixture content."""
        result = extract_item1_business(self.apple_html)

        assert result is not None
        # The beginning should match the expected fixture content
        assert "Company Background" in result
        assert "designs, manufactures and markets smartphones" in result

        # Verify length is in a reasonable range compared to expected
        expected_text = self.expected_data["item1_business_text"]
        assert abs(len(result) - len(expected_text)) < 1000  # Should be close in length

    def test_key_phrases_are_present(self):
        """Key phrases from the business description should be present."""
        result = extract_item1_business(self.apple_html)

        # Check for key business description phrases
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
    os.environ.get("RUN_LIVE_API_TESTS") != "true",
    reason="Live API tests disabled. Set RUN_LIVE_API_TESTS=true to run.",
)
class TestLiveAPIBusinessDescription(unittest.TestCase):
    """Live API tests for SEC EDGAR data source.

    These tests make actual network requests to SEC EDGAR.
    Set RUN_LIVE_API_TESTS=true to run them.
    """

    def setUp(self):
        self.source = SECEdgarDataSource(
            user_agent="ISW Test admin@example.com",
            timeout=60.0,
        )
        self.apple_cik = "0000320193"

    def test_fetches_apple_filings(self):
        """Should fetch filing list from SEC for Apple."""
        filings = self.source.list_filings(self.apple_cik, limit=5)

        assert len(filings) > 0
        assert filings[0].identifier == self.apple_cik

    def test_fetches_apple_10k(self):
        """Should fetch latest 10-K filing for Apple."""
        filing = self.source.get_latest_annual_filing(self.apple_cik)

        assert filing is not None
        assert filing.filing_type == "10-K"
        assert filing.document_url is not None

    def test_fetches_apple_business_description(self):
        """Should fetch and extract business description for Apple."""
        description = self.source.get_business_description(self.apple_cik)

        assert description is not None
        assert len(description.text) > 5000
        assert "designs, manufactures" in description.text
        assert description.source_filing_type == "10-K"
        assert description.extraction_method == "html_parse"

    def test_fetches_apple_revenue(self):
        """Should fetch revenue data for Apple from company facts API."""
        revenue = self.source.get_revenue(self.apple_cik)

        assert revenue is not None
        assert revenue.currency == "USD"
        assert revenue.amount > 300_000_000_000  # > $300B
