"""Unit tests for FilingsXBRLDataSource internal methods."""

import unittest

from isw.core.services.data_sources.esef_data_source import (
    BUSINESS_DESCRIPTION_TAG,
    REVENUE_TAG,
    FilingsXBRLDataSource,
)


class TestSupportsIdentifier(unittest.TestCase):
    def setUp(self):
        self.source = FilingsXBRLDataSource()

    def test_valid_lei_20_alphanumeric(self):
        assert self.source.supports_identifier("213800H2PQMIF3OVZY47") is True

    def test_valid_lei_all_digits(self):
        assert self.source.supports_identifier("12345678901234567890") is True

    def test_invalid_lei_too_short(self):
        assert self.source.supports_identifier("213800H2PQMIF3OVZY4") is False

    def test_invalid_lei_too_long(self):
        assert self.source.supports_identifier("213800H2PQMIF3OVZY477") is False

    def test_invalid_lei_special_characters(self):
        assert self.source.supports_identifier("213800H2PQMIF3OV-Y47") is False

    def test_invalid_cik_format(self):
        assert self.source.supports_identifier("0000320193") is False


class TestExtractFactByConcept(unittest.TestCase):
    def setUp(self):
        self.source = FilingsXBRLDataSource()

    def test_extracts_business_description(self):
        xbrl_data = {
            "facts": {
                "fact-1": {
                    "value": "Company provides digital services.",
                    "dimensions": {"concept": BUSINESS_DESCRIPTION_TAG},
                }
            }
        }

        result = self.source._extract_fact_by_concept(xbrl_data, BUSINESS_DESCRIPTION_TAG)
        assert result == "Company provides digital services."

    def test_returns_none_when_concept_not_found(self):
        xbrl_data = {
            "facts": {
                "fact-1": {
                    "value": "Some other value",
                    "dimensions": {"concept": "ifrs-full:OtherConcept"},
                }
            }
        }

        result = self.source._extract_fact_by_concept(xbrl_data, BUSINESS_DESCRIPTION_TAG)
        assert result is None

    def test_returns_none_for_empty_facts(self):
        xbrl_data = {"facts": {}}
        result = self.source._extract_fact_by_concept(xbrl_data, BUSINESS_DESCRIPTION_TAG)
        assert result is None


class TestFindMostRecentRevenueFact(unittest.TestCase):
    def setUp(self):
        self.source = FilingsXBRLDataSource()

    def test_finds_most_recent_revenue(self):
        facts = {
            "fact-10": {
                "value": "100000000",
                "dimensions": {
                    "concept": REVENUE_TAG,
                    "period": "2020-04-01T00:00:00/2021-04-01T00:00:00",
                    "unit": "iso4217:GBP",
                },
            },
            "fact-11": {
                "value": "150000000",
                "dimensions": {
                    "concept": REVENUE_TAG,
                    "period": "2021-04-01T00:00:00/2022-04-01T00:00:00",
                    "unit": "iso4217:GBP",
                },
            },
        }

        result = self.source._find_most_recent_revenue_fact(facts)
        assert result["value"] == "150000000"

    def test_returns_none_when_no_revenue_facts(self):
        facts = {
            "fact-1": {
                "value": "Some value",
                "dimensions": {"concept": "ifrs-full:OtherConcept"},
            }
        }

        result = self.source._find_most_recent_revenue_fact(facts)
        assert result is None

    def test_ignores_point_in_time_periods(self):
        facts = {
            "fact-10": {
                "value": "100000000",
                "dimensions": {
                    "concept": REVENUE_TAG,
                    "period": "2022-04-01T00:00:00",  # Point in time, no slash
                },
            }
        }

        result = self.source._find_most_recent_revenue_fact(facts)
        assert result is None


class TestParseRevenueFact(unittest.TestCase):
    def setUp(self):
        self.source = FilingsXBRLDataSource()

    def test_parses_revenue_fact(self):
        fact = {
            "value": "302632000",
            "dimensions": {
                "concept": REVENUE_TAG,
                "unit": "iso4217:GBP",
            },
        }

        result = self.source._parse_revenue_fact(fact, "2022-03-31")
        assert result is not None
        assert result.amount == 302632000
        assert result.currency == "GBP"
        assert result.period_end == "2022-03-31"
        assert result.source_tag == REVENUE_TAG

    def test_parses_float_revenue_value(self):
        fact = {
            "value": "367246000.0",
            "dimensions": {
                "concept": REVENUE_TAG,
                "unit": "iso4217:GBP",
            },
        }

        result = self.source._parse_revenue_fact(fact, "2025-03-31")
        assert result is not None
        assert result.amount == 367246000

    def test_returns_none_for_missing_value(self):
        fact = {"dimensions": {"unit": "iso4217:GBP"}}
        result = self.source._parse_revenue_fact(fact, "2022-03-31")
        assert result is None

    def test_returns_none_for_invalid_value(self):
        fact = {"value": "not-a-number", "dimensions": {"unit": "iso4217:GBP"}}
        result = self.source._parse_revenue_fact(fact, "2022-03-31")
        assert result is None


class TestExtractCurrencyFromUnit(unittest.TestCase):
    def setUp(self):
        self.source = FilingsXBRLDataSource()

    def test_extracts_gbp(self):
        assert self.source._extract_currency_from_unit("iso4217:GBP") == "GBP"

    def test_extracts_eur(self):
        assert self.source._extract_currency_from_unit("iso4217:EUR") == "EUR"

    def test_extracts_usd(self):
        assert self.source._extract_currency_from_unit("iso4217:USD") == "USD"

    def test_handles_plain_currency(self):
        assert self.source._extract_currency_from_unit("GBP") == "GBP"

    def test_handles_empty_string(self):
        assert self.source._extract_currency_from_unit("") == "Unknown"


class TestParseFiling(unittest.TestCase):
    def setUp(self):
        self.source = FilingsXBRLDataSource()

    def test_parses_valid_filing(self):
        item = {
            "attributes": {
                "period_end": "2022-03-31",
                "report_url": "/213800H2/reports/report.xhtml",
                "json_url": "/213800H2/report.json",
                "viewer_url": "/213800H2/viewer.html",
                "country": "GB",
            }
        }

        result = self.source._parse_filing(item, "213800H2PQMIF3OVZY47")
        assert result is not None
        assert result.identifier == "213800H2PQMIF3OVZY47"
        assert result.filing_type == "AFR"
        assert result.period_end == "2022-03-31"
        assert result.raw_data["json_url"] == "/213800H2/report.json"
        assert result.raw_data["country"] == "GB"

    def test_returns_none_for_missing_period_end(self):
        item = {"attributes": {"report_url": "/reports/report.xhtml"}}
        result = self.source._parse_filing(item, "213800H2PQMIF3OVZY47")
        assert result is None
