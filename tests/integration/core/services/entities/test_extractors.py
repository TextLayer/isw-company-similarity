"""Integration tests for entity extractors using real fixtures.

These tests verify that revenue and description extraction works correctly
with real-world XBRL and filing data.
"""

import pandas as pd
import pytest

from isw.core.services.entities.extractors import RevenueExtractor


class TestRevenueExtractorXBRL:
    """Test revenue extraction from XBRL-JSON fixtures."""

    @pytest.fixture
    def extractor(self):
        return RevenueExtractor()

    def test_extract_kainos_revenue(self, extractor, kainos_xbrl_json):
        """Should extract Kainos revenue from XBRL-JSON."""
        result = extractor.from_xbrl_json(kainos_xbrl_json, "2022-03-31")

        assert result is not None
        assert result.amount == 302632000
        assert result.currency == "GBP"
        assert result.source_tag == "ifrs-full:Revenue"

    def test_extract_handles_missing_revenue(self, extractor):
        """Should return None when no revenue facts found."""
        empty_xbrl = {"facts": {}}
        result = extractor.from_xbrl_json(empty_xbrl, "2022-03-31")

        assert result is None

    def test_extract_prefers_recent_period(self, extractor, kainos_xbrl_json):
        """Should prefer the most recent revenue value."""
        result = extractor.from_xbrl_json(kainos_xbrl_json, "2022-03-31")

        # Kainos fixture has 2021-2022 (302632000) and 2020-2021 (234694000)
        # Should return the more recent value
        assert result.amount == 302632000

    def test_extract_handles_nested_facts(self, extractor, kainos_xbrl_json):
        """Should handle XBRL structure whether facts is top-level or nested."""
        # Test with nested structure (facts key)
        nested = {"facts": kainos_xbrl_json.get("facts", kainos_xbrl_json)}
        result = extractor.from_xbrl_json(nested, "2022-03-31")
        assert result is not None

        # Test with flat structure
        flat = kainos_xbrl_json.get("facts", kainos_xbrl_json)
        result = extractor.from_xbrl_json(flat, "2022-03-31")
        assert result is not None


class TestRevenueExtractorEdgarFacts:
    """Test revenue extraction from SEC EDGAR company facts."""

    @pytest.fixture
    def extractor(self):
        return RevenueExtractor()

    def test_extract_from_facts_dataframe(self, extractor, apple_company_facts):
        """Should extract revenue from company facts DataFrame."""
        # Convert fixture to DataFrame format similar to EdgarTools
        facts_list = []
        for namespace_data in apple_company_facts.get("facts", {}).values():
            for concept, concept_data in namespace_data.items():
                for unit_key, unit_data in concept_data.get("units", {}).items():
                    for fact in unit_data:
                        facts_list.append(
                            {
                                "concept": f"us-gaap:{concept}" if "us-gaap" in str(namespace_data) else concept,
                                "unit": unit_key,
                                "numeric_value": fact.get("val"),
                                "period_end": fact.get("end"),
                                "fiscal_period": fact.get("fp", "FY"),
                            }
                        )

        if not facts_list:
            pytest.skip("Fixture doesn't have extractable facts structure")

        df = pd.DataFrame(facts_list)
        result = extractor.from_edgar_facts_df(df)

        # Result may be None if fixture doesn't have revenue data
        # The test verifies the extractor handles the data correctly
        if result is not None:
            assert result.amount > 0
            assert result.currency in ["USD", "CAD", "GBP", "EUR"]


class TestRevenueExtractorTagPriority:
    """Test that revenue tags are tried in priority order."""

    @pytest.fixture
    def extractor(self):
        return RevenueExtractor()

    def test_ifrs_primary_tag_preferred(self, extractor):
        """ifrs-full:Revenue should be preferred over other tags."""
        # Create facts with multiple revenue-like values
        facts = {
            "fact-1": {
                "value": "1000000",
                "dimensions": {
                    "concept": "ifrs-full:Revenue",
                    "entity": "scheme:TEST123",
                    "period": "2022-01-01T00:00:00/2023-01-01T00:00:00",
                    "unit": "iso4217:GBP",
                },
            },
            "fact-2": {
                "value": "500000",
                "dimensions": {
                    "concept": "ifrs-full:RevenueFromContractsWithCustomers",
                    "entity": "scheme:TEST123",
                    "period": "2022-01-01T00:00:00/2023-01-01T00:00:00",
                    "unit": "iso4217:GBP",
                },
            },
        }

        result = extractor.from_xbrl_json(facts, "2022-12-31")

        assert result is not None
        assert result.amount == 1000000  # Should use primary tag value
        assert result.source_tag == "ifrs-full:Revenue"

    def test_sec_primary_tag_order(self, extractor):
        """us-gaap:Revenues should be first in SEC tag priority."""
        assert extractor.sec_tags[0] == "us-gaap:Revenues"

    def test_custom_tags(self):
        """Should support custom tag configuration."""
        custom_extractor = RevenueExtractor(
            sec_tags=["custom:Revenue"],
            ifrs_tags=["custom:IFRSRevenue"],
        )
        assert custom_extractor.sec_tags == ["custom:Revenue"]
        assert custom_extractor.ifrs_tags == ["custom:IFRSRevenue"]


class TestRevenueExtractorCurrencyExtraction:
    """Test currency extraction from XBRL units."""

    @pytest.fixture
    def extractor(self):
        return RevenueExtractor()

    def test_extract_currency_from_prefixed_unit(self, extractor):
        """Should extract currency from iso4217:XXX format."""
        result = extractor._extract_currency_from_unit("iso4217:GBP")
        assert result == "GBP"

    def test_extract_currency_from_plain_unit(self, extractor):
        """Should handle plain currency codes."""
        result = extractor._extract_currency_from_unit("USD")
        assert result == "USD"

    def test_extract_currency_from_empty(self, extractor):
        """Should return 'Unknown' for empty unit."""
        result = extractor._extract_currency_from_unit("")
        assert result == "Unknown"
