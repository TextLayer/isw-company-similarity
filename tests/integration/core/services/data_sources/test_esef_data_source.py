"""Integration tests for FilingsXBRLDataSource using real XBRL data.

These tests verify that the ESEF data source correctly extracts
business descriptions and revenue data from real XBRL-JSON files.
"""

import json
import os
import unittest
from pathlib import Path

import pytest

from isw.core.services.data_sources.base import BusinessDescription, RevenueData
from isw.core.services.data_sources.esef_data_source import (
    BUSINESS_DESCRIPTION_TAG,
    REVENUE_TAG,
    FilingsXBRLDataSource,
)

FIXTURES_DIR = Path(__file__).parent.parent.parent.parent.parent / "fixtures"
XBRL_JSON_FIXTURES = FIXTURES_DIR / "data_sources" / "real_xbrl_json"


class TestBusinessDescriptionFromRealXBRL(unittest.TestCase):
    """Test business description extraction from real XBRL-JSON."""

    @classmethod
    def setUpClass(cls):
        if not XBRL_JSON_FIXTURES.exists():
            raise unittest.SkipTest("XBRL JSON fixtures not available")

        kainos_path = XBRL_JSON_FIXTURES / "kainos_2022.json"
        if not kainos_path.exists():
            raise unittest.SkipTest("Kainos fixture not available")

        with open(kainos_path) as f:
            cls.kainos_xbrl = json.load(f)

    def setUp(self):
        self.source = FilingsXBRLDataSource()

    def test_extracts_kainos_business_description(self):
        text = self.source._extract_fact_by_concept(self.kainos_xbrl, BUSINESS_DESCRIPTION_TAG)

        assert text is not None
        assert len(text) > 100
        assert "Digital Services" in text
        assert "Workday" in text

    def test_business_description_is_comprehensive(self):
        text = self.source._extract_fact_by_concept(self.kainos_xbrl, BUSINESS_DESCRIPTION_TAG)

        assert "custom digital service platforms" in text
        assert "public sector" in text or "commercial" in text or "healthcare" in text

    def test_extracts_company_name(self):
        name = self.source._extract_fact_by_concept(
            self.kainos_xbrl,
            "ifrs-full:NameOfReportingEntityOrOtherMeansOfIdentification",
        )

        assert name == "Kainos Group plc"

    def test_extracts_country_of_incorporation(self):
        country = self.source._extract_fact_by_concept(self.kainos_xbrl, "ifrs-full:CountryOfIncorporation")

        assert country == "United Kingdom"


class TestRevenueFromRealXBRL(unittest.TestCase):
    """Test revenue extraction from real XBRL-JSON."""

    @classmethod
    def setUpClass(cls):
        if not XBRL_JSON_FIXTURES.exists():
            raise unittest.SkipTest("XBRL JSON fixtures not available")

        kainos_path = XBRL_JSON_FIXTURES / "kainos_2022.json"
        if not kainos_path.exists():
            raise unittest.SkipTest("Kainos fixture not available")

        with open(kainos_path) as f:
            cls.kainos_xbrl = json.load(f)

    def setUp(self):
        self.source = FilingsXBRLDataSource()

    def test_extracts_kainos_revenue(self):
        facts = self.kainos_xbrl.get("facts", {})
        revenue_fact = self.source._find_most_recent_revenue_fact(facts)

        assert revenue_fact is not None
        assert revenue_fact["value"] == "302632000"

    def test_parses_revenue_correctly(self):
        facts = self.kainos_xbrl.get("facts", {})
        revenue_fact = self.source._find_most_recent_revenue_fact(facts)
        revenue = self.source._parse_revenue_fact(revenue_fact, "2022-03-31")

        assert revenue is not None
        assert revenue.amount == 302632000
        assert revenue.currency == "GBP"
        assert revenue.period_end == "2022-03-31"
        assert revenue.source_tag == REVENUE_TAG

    def test_revenue_is_reasonable_value(self):
        facts = self.kainos_xbrl.get("facts", {})
        revenue_fact = self.source._find_most_recent_revenue_fact(facts)
        revenue = self.source._parse_revenue_fact(revenue_fact, "2022-03-31")

        assert revenue.amount > 100_000_000
        assert revenue.amount < 10_000_000_000


@pytest.mark.skipif(
    os.environ.get("RUN_LIVE_API_TESTS") != "1",
    reason="Set RUN_LIVE_API_TESTS=1 to run live API tests",
)
class TestLiveAPIBusinessDescription(unittest.TestCase):
    """Test against live filings.xbrl.org API.

    Run with: RUN_LIVE_API_TESTS=1 pytest tests/integration/.../test_esef_data_source.py
    """

    def setUp(self):
        self.source = FilingsXBRLDataSource()

    def test_fetches_kainos_filings(self):
        filings = self.source.list_filings("213800H2PQMIF3OVZY47", limit=3)

        assert len(filings) > 0
        assert filings[0].identifier == "213800H2PQMIF3OVZY47"
        assert filings[0].filing_type == "AFR"
        assert filings[0].period_end

    def test_fetches_kainos_business_description(self):
        desc = self.source.get_business_description("213800H2PQMIF3OVZY47")

        assert desc is not None
        assert isinstance(desc, BusinessDescription)
        assert "Digital Services" in desc.text or "Workday" in desc.text
        assert desc.source_filing_type == "AFR"
        assert desc.extraction_method == "xbrl_extract"

    def test_fetches_kainos_revenue(self):
        revenue = self.source.get_revenue("213800H2PQMIF3OVZY47")

        assert revenue is not None
        assert isinstance(revenue, RevenueData)
        assert revenue.amount > 0
        assert revenue.currency in ("GBP", "EUR", "USD")
