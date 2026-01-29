"""Unit tests for SEC EDGAR collector internal logic.

These tests focus on complex internal logic like date filtering.
Integration tests cover data parsing from realistic fixtures.
"""

import unittest

from isw.core.services.entity_collection import SECEdgarCollector


class TestSECEdgarCollectorLogic(unittest.TestCase):
    """Unit tests for SECEdgarCollector internal logic."""

    def test_has_recent_10k_with_recent_filing(self):
        """Test detection of recent 10-K filing."""
        collector = SECEdgarCollector(user_agent="test/1.0", years_lookback=3)

        submission = {
            "filings": {
                "recent": {
                    "form": ["10-K", "10-Q", "8-K"],
                    "filingDate": ["2025-03-15", "2024-11-15", "2024-08-15"],
                }
            }
        }

        assert collector._has_recent_10k(submission) is True

    def test_has_recent_10k_with_amendment(self):
        """Test that 10-K/A (amended) filings are counted."""
        collector = SECEdgarCollector(user_agent="test/1.0")

        submission = {
            "filings": {
                "recent": {
                    "form": ["10-K/A", "10-Q"],
                    "filingDate": ["2025-04-15", "2024-11-15"],
                }
            }
        }

        assert collector._has_recent_10k(submission) is True

    def test_has_recent_10k_with_old_filing(self):
        """Test that old 10-K filings are not counted."""
        collector = SECEdgarCollector(user_agent="test/1.0", years_lookback=3)

        submission = {
            "filings": {
                "recent": {
                    "form": ["10-K"],
                    "filingDate": ["2020-03-15"],
                }
            }
        }

        assert collector._has_recent_10k(submission) is False

    def test_has_recent_10k_empty_filings(self):
        """Test handling of empty filings."""
        collector = SECEdgarCollector(user_agent="test/1.0")

        submission = {"filings": {"recent": {"form": [], "filingDate": []}}}

        assert collector._has_recent_10k(submission) is False

    def test_has_recent_10k_no_10k_forms(self):
        """Test that non-10K forms are not counted."""
        collector = SECEdgarCollector(user_agent="test/1.0")

        submission = {
            "filings": {
                "recent": {
                    "form": ["10-Q", "8-K", "DEF 14A"],
                    "filingDate": ["2025-03-15", "2025-02-15", "2025-01-15"],
                }
            }
        }

        assert collector._has_recent_10k(submission) is False

    def test_has_recent_10k_invalid_date_format(self):
        """Test handling of invalid date formats."""
        collector = SECEdgarCollector(user_agent="test/1.0")

        submission = {
            "filings": {
                "recent": {
                    "form": ["10-K"],
                    "filingDate": ["invalid-date"],
                }
            }
        }

        assert collector._has_recent_10k(submission) is False

    def test_get_source_name(self):
        """Test source name is correct."""
        collector = SECEdgarCollector(user_agent="test/1.0")
        assert collector.get_source_name() == "SEC EDGAR"
