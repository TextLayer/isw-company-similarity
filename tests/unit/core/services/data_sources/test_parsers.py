"""Unit tests for SEC filing parsers.

Tests the shared parsing utilities using real SEC filing fixtures.
"""

import json
import unittest
from pathlib import Path

from isw.core.services.data_sources.parsers import (
    clean_extracted_text,
    extract_item1_business,
)

REAL_SEC_FIXTURES = Path(__file__).parent.parent.parent.parent.parent / "fixtures" / "data_sources" / "real_sec_data"


class TestExtractItem1Business(unittest.TestCase):
    """Tests for Item 1. Business extraction from real 10-K HTML."""

    @classmethod
    def setUpClass(cls):
        """Load real Apple 10-K HTML fixture."""
        html_path = REAL_SEC_FIXTURES / "apple_10k_2025.htm"
        if not html_path.exists():
            raise unittest.SkipTest("Real SEC HTML fixture not available")

        with open(html_path) as f:
            cls.apple_html = f.read()

        # Load expected content for comparison
        item1_path = REAL_SEC_FIXTURES / "apple_10k_item1_business.json"
        if item1_path.exists():
            with open(item1_path) as f:
                cls.expected_data = json.load(f)
        else:
            cls.expected_data = None

    def test_extracts_substantial_content(self):
        """Should extract substantial content from Item 1 section."""
        result = extract_item1_business(self.apple_html)

        assert result is not None
        # Item 1. Business should be several thousand characters
        assert len(result) > 5000

    def test_starts_with_company_background(self):
        """Extracted text should start with company description."""
        result = extract_item1_business(self.apple_html)

        assert result is not None
        assert "Company Background" in result

    def test_contains_core_business_description(self):
        """Should contain the core business description."""
        result = extract_item1_business(self.apple_html)

        assert result is not None
        assert "designs, manufactures and markets" in result
        assert "smartphones" in result

    def test_contains_product_categories(self):
        """Should contain all major product categories."""
        result = extract_item1_business(self.apple_html)

        assert result is not None
        assert "iPhone" in result
        assert "Mac" in result
        assert "iPad" in result
        assert "Wearables" in result

    def test_contains_services_section(self):
        """Should contain services information."""
        result = extract_item1_business(self.apple_html)

        assert result is not None
        assert "Services" in result
        assert "App Store" in result
        assert "AppleCare" in result

    def test_contains_segment_information(self):
        """Should contain geographic segment information."""
        result = extract_item1_business(self.apple_html)

        assert result is not None
        assert "Americas" in result
        assert "Europe" in result
        assert "Greater China" in result

    def test_excludes_table_of_contents(self):
        """Should not include table of contents."""
        result = extract_item1_business(self.apple_html)

        assert result is not None
        assert "TABLE OF CONTENTS" not in result

    def test_excludes_risk_factors(self):
        """Should stop before Risk Factors section."""
        result = extract_item1_business(self.apple_html)

        assert result is not None
        # This phrase appears in the Risk Factors section
        assert "operations and performance depend significantly on global" not in result

    def test_length_matches_expected_fixture(self):
        """Extracted length should be close to expected fixture."""
        if self.expected_data is None:
            self.skipTest("Expected data fixture not available")

        result = extract_item1_business(self.apple_html)
        expected_text = self.expected_data["item1_business_text"]

        assert result is not None
        # Allow some variance for whitespace differences
        assert abs(len(result) - len(expected_text)) < 1000

    def test_returns_none_for_empty_html(self):
        """Should return None for empty HTML."""
        result = extract_item1_business("")
        assert result is None

    def test_returns_none_for_html_without_item1(self):
        """Should return None for HTML without Item 1 section."""
        html = "<html><body><h1>Some Document</h1><p>No item 1 here.</p></body></html>"
        result = extract_item1_business(html)
        assert result is None


class TestCleanExtractedText(unittest.TestCase):
    """Tests for text cleaning using real extracted content."""

    @classmethod
    def setUpClass(cls):
        """Load expected Item 1 fixture for realistic test data."""
        item1_path = REAL_SEC_FIXTURES / "apple_10k_item1_business.json"
        if not item1_path.exists():
            raise unittest.SkipTest("Item 1 fixture not available")

        with open(item1_path) as f:
            data = json.load(f)
            cls.real_text = data["item1_business_text"]

    def test_preserves_real_content(self):
        """Cleaning real content should preserve the essential text."""
        result = clean_extracted_text(self.real_text)

        # Core content should be preserved
        assert "Company Background" in result
        assert "iPhone" in result
        assert "Services" in result

    def test_removes_standalone_page_numbers(self):
        """Should remove lines that are just page numbers."""
        text_with_page_numbers = "Some content\n\n42\n\nMore content\n\n17\n\nEnd"
        result = clean_extracted_text(text_with_page_numbers)

        assert "42" not in result
        assert "17" not in result
        assert "Some content" in result
        assert "More content" in result

    def test_normalizes_excessive_newlines(self):
        """Should collapse excessive newlines to double newlines."""
        text_with_many_newlines = "First paragraph\n\n\n\n\n\nSecond paragraph"
        result = clean_extracted_text(text_with_many_newlines)

        assert "\n\n\n" not in result
        assert "First paragraph" in result
        assert "Second paragraph" in result

    def test_strips_whitespace(self):
        """Should strip leading and trailing whitespace."""
        text_with_whitespace = "   \n\nContent here\n\n   "
        result = clean_extracted_text(text_with_whitespace)

        assert result == "Content here"

    def test_removes_sec_boilerplate(self):
        """Should remove SEC filing boilerplate headers."""
        text_with_boilerplate = "Apple Inc. | 2025 Form 10-K | 1\nActual content here"
        result = clean_extracted_text(text_with_boilerplate)

        assert "| 2025 Form 10-K |" not in result
        assert "Actual content here" in result
