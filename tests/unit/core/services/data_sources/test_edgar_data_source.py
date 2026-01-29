"""Unit tests for SEC EDGAR data source.

Tests internal logic and helper methods of the SECEdgarDataSource class.
These tests do not make network requests - they test parsing and extraction logic.
"""

import unittest

from isw.core.services.data_sources.edgar_data_source import SECEdgarDataSource
from isw.core.services.data_sources.parsers import clean_extracted_text


class TestSupportsIdentifier(unittest.TestCase):
    """Tests for CIK identifier validation."""

    def setUp(self):
        self.source = SECEdgarDataSource(user_agent="Test test@example.com")

    def test_valid_cik_with_leading_zeros(self):
        """Valid CIK with leading zeros should be supported."""
        assert self.source.supports_identifier("0000320193") is True

    def test_valid_cik_without_leading_zeros(self):
        """Valid CIK without leading zeros should be supported."""
        assert self.source.supports_identifier("320193") is True

    def test_valid_single_digit_cik(self):
        """Single digit CIK should be supported."""
        assert self.source.supports_identifier("1") is True

    def test_rejects_non_numeric(self):
        """Non-numeric identifier should be rejected."""
        assert self.source.supports_identifier("ABC123") is False

    def test_rejects_empty_string(self):
        """Empty string should be rejected."""
        assert self.source.supports_identifier("") is False

    def test_rejects_lei_format(self):
        """LEI format (20 alphanumeric chars) should be rejected."""
        assert self.source.supports_identifier("213800WA8HCQCJ4YCL71") is False

    def test_rejects_too_long(self):
        """CIK longer than 10 digits (excluding leading zeros) should be rejected."""
        assert self.source.supports_identifier("12345678901") is False


class TestNormalizeCik(unittest.TestCase):
    """Tests for CIK normalization."""

    def setUp(self):
        self.source = SECEdgarDataSource(user_agent="Test test@example.com")

    def test_pads_short_cik(self):
        """Short CIK should be padded to 10 digits."""
        assert self.source._normalize_cik("320193") == "0000320193"

    def test_preserves_full_length_cik(self):
        """Already 10-digit CIK should be preserved."""
        assert self.source._normalize_cik("0000320193") == "0000320193"

    def test_pads_single_digit(self):
        """Single digit should be padded."""
        assert self.source._normalize_cik("1") == "0000000001"


class TestExtractRevenueFromFacts(unittest.TestCase):
    """Tests for revenue extraction from company facts data."""

    def setUp(self):
        self.source = SECEdgarDataSource(user_agent="Test test@example.com")

    def test_extracts_revenues_tag(self):
        """Should extract revenue from Revenues tag."""
        facts_data = {
            "facts": {
                "us-gaap": {
                    "Revenues": {
                        "units": {
                            "USD": [
                                {"val": 383285000000, "end": "2023-09-30", "form": "10-K"},
                                {"val": 394328000000, "end": "2022-10-01", "form": "10-K"},
                            ]
                        }
                    }
                }
            }
        }
        result = self.source._extract_revenue_from_facts(facts_data)
        assert result is not None
        assert result.amount == 383285000000
        assert result.currency == "USD"
        assert result.period_end == "2023-09-30"
        assert result.source_tag == "us-gaap:Revenues"

    def test_prefers_revenues_over_alternatives(self):
        """Should prefer Revenues tag over alternative tags."""
        facts_data = {
            "facts": {
                "us-gaap": {
                    "Revenues": {
                        "units": {
                            "USD": [
                                {"val": 100000000, "end": "2023-09-30", "form": "10-K"},
                            ]
                        }
                    },
                    "SalesRevenueNet": {
                        "units": {
                            "USD": [
                                {"val": 200000000, "end": "2023-09-30", "form": "10-K"},
                            ]
                        }
                    },
                }
            }
        }
        result = self.source._extract_revenue_from_facts(facts_data)
        assert result is not None
        assert result.amount == 100000000
        assert result.source_tag == "us-gaap:Revenues"

    def test_skips_quarterly_filings(self):
        """Should only use 10-K (annual) values, not 10-Q (quarterly)."""
        facts_data = {
            "facts": {
                "us-gaap": {
                    "Revenues": {
                        "units": {
                            "USD": [
                                {"val": 90000000, "end": "2023-12-30", "form": "10-Q"},
                                {"val": 383285000000, "end": "2023-09-30", "form": "10-K"},
                            ]
                        }
                    }
                }
            }
        }
        result = self.source._extract_revenue_from_facts(facts_data)
        assert result is not None
        assert result.amount == 383285000000

    def test_returns_none_for_empty_facts(self):
        """Should return None if no facts are available."""
        facts_data = {"facts": {}}
        result = self.source._extract_revenue_from_facts(facts_data)
        assert result is None

    def test_returns_none_for_no_usd_values(self):
        """Should return None if no USD values are available."""
        facts_data = {
            "facts": {
                "us-gaap": {
                    "Revenues": {
                        "units": {
                            "EUR": [
                                {"val": 100000000, "end": "2023-09-30", "form": "10-K"},
                            ]
                        }
                    }
                }
            }
        }
        result = self.source._extract_revenue_from_facts(facts_data)
        assert result is None


class TestParseFilings(unittest.TestCase):
    """Tests for parsing filings from SEC submissions API response."""

    def setUp(self):
        self.source = SECEdgarDataSource(user_agent="Test test@example.com")

    def test_parses_10k_filing(self):
        """Should parse 10-K filing data correctly."""
        data = {
            "filings": {
                "recent": {
                    "form": ["10-K", "10-Q", "8-K"],
                    "accessionNumber": [
                        "0000320193-25-000079",
                        "0000320193-25-000073",
                        "0000320193-25-000071",
                    ],
                    "filingDate": ["2025-10-31", "2025-08-01", "2025-07-15"],
                    "reportDate": ["2025-09-27", "2025-06-28", "2025-07-01"],
                    "primaryDocument": [
                        "aapl-20250927.htm",
                        "aapl-20250628.htm",
                        "form8k.htm",
                    ],
                }
            }
        }

        result = self.source._parse_filings(data, "0000320193", "10-K", 10)
        assert len(result) == 1
        filing = result[0]
        assert filing.filing_type == "10-K"
        assert filing.period_end == "2025-09-27"
        assert filing.accession_number == "0000320193-25-000079"
        assert "320193" in filing.document_url
        assert "000032019325000079" in filing.document_url
        assert "aapl-20250927.htm" in filing.document_url

    def test_respects_limit(self):
        """Should respect the limit parameter."""
        data = {
            "filings": {
                "recent": {
                    "form": ["10-K", "10-K", "10-K"],
                    "accessionNumber": ["acc1", "acc2", "acc3"],
                    "filingDate": ["2025-01-01", "2024-01-01", "2023-01-01"],
                    "reportDate": ["2024-12-31", "2023-12-31", "2022-12-31"],
                    "primaryDocument": ["doc1.htm", "doc2.htm", "doc3.htm"],
                }
            }
        }

        result = self.source._parse_filings(data, "0000320193", "10-K", 2)
        assert len(result) == 2

    def test_filters_by_filing_type(self):
        """Should filter by filing type when specified."""
        data = {
            "filings": {
                "recent": {
                    "form": ["10-K", "10-Q", "10-K"],
                    "accessionNumber": ["acc1", "acc2", "acc3"],
                    "filingDate": ["2025-01-01", "2024-10-01", "2024-01-01"],
                    "reportDate": ["2024-12-31", "2024-09-30", "2023-12-31"],
                    "primaryDocument": ["doc1.htm", "doc2.htm", "doc3.htm"],
                }
            }
        }

        result = self.source._parse_filings(data, "0000320193", "10-K", 10)
        assert len(result) == 2
        for filing in result:
            assert filing.filing_type == "10-K"


class TestCleanExtractedText(unittest.TestCase):
    """Tests for text cleaning after extraction."""

    def test_removes_page_numbers(self):
        """Should remove standalone page numbers."""
        text = "Some content\n\n42\n\nMore content"
        result = clean_extracted_text(text)
        assert "42" not in result
        assert "Some content" in result
        assert "More content" in result

    def test_normalizes_whitespace(self):
        """Should normalize excessive newlines."""
        text = "First paragraph\n\n\n\n\n\nSecond paragraph"
        result = clean_extracted_text(text)
        assert "\n\n\n" not in result

    def test_strips_empty_lines(self):
        """Should strip leading/trailing whitespace."""
        text = "   \n\nContent here\n\n   "
        result = clean_extracted_text(text)
        assert result == "Content here"
