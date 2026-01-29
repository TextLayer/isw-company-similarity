import json
import unittest

from isw.core.services.data_sources.parsers import (
    clean_extracted_text,
    parse_10k_business_section,
)
from tests.conftest import get_fixture_path

SEC_FIXTURES = get_fixture_path("data_sources", "sec_data")


class TestParse10kBusinessSection(unittest.TestCase):
    """Tests for Item 1. Business extraction from 10-K HTML."""

    @classmethod
    def setUpClass(cls):
        html_path = SEC_FIXTURES / "apple_10k_2025.htm"
        if not html_path.exists():
            raise unittest.SkipTest("SEC HTML fixture not available")

        with open(html_path) as f:
            cls.apple_html = f.read()

        item1_path = SEC_FIXTURES / "apple_10k_item1_business.json"
        if item1_path.exists():
            with open(item1_path) as f:
                cls.expected_data = json.load(f)
        else:
            cls.expected_data = None

    def test_extracts_substantial_content(self):
        result = parse_10k_business_section(self.apple_html)

        assert result is not None
        assert len(result) > 500

    def test_starts_with_company_background(self):
        result = parse_10k_business_section(self.apple_html)

        assert result is not None
        assert "Company Background" in result

    def test_contains_core_business_description(self):
        result = parse_10k_business_section(self.apple_html)

        assert result is not None
        assert "designs, manufactures and markets" in result
        assert "smartphones" in result

    def test_contains_product_categories(self):
        result = parse_10k_business_section(self.apple_html)

        assert result is not None
        assert "iPhone" in result
        assert "Mac" in result
        assert "iPad" in result
        assert "Wearables" in result

    def test_contains_services_section(self):
        result = parse_10k_business_section(self.apple_html)

        assert result is not None
        assert "Services" in result
        assert "App Store" in result
        assert "AppleCare" in result

    def test_contains_segment_information(self):
        result = parse_10k_business_section(self.apple_html)

        assert result is not None
        assert "Americas" in result
        assert "Europe" in result
        assert "Greater China" in result

    def test_excludes_table_of_contents(self):
        result = parse_10k_business_section(self.apple_html)

        assert result is not None
        assert "TABLE OF CONTENTS" not in result

    def test_excludes_risk_factors(self):
        result = parse_10k_business_section(self.apple_html)

        assert result is not None
        assert "operations and performance depend significantly on global" not in result

    def test_length_matches_expected_fixture(self):
        if self.expected_data is None:
            self.skipTest("Expected data fixture not available")

        result = parse_10k_business_section(self.apple_html)
        expected_text = self.expected_data["item1_business_text"]

        assert result is not None
        assert abs(len(result) - len(expected_text)) < 1000

    def test_returns_none_for_empty_html(self):
        result = parse_10k_business_section("")
        assert result is None

    def test_returns_none_for_html_without_item1(self):
        html = "<html><body><h1>Some Document</h1><p>No item 1 here.</p></body></html>"
        result = parse_10k_business_section(html)
        assert result is None


class TestCleanExtractedText(unittest.TestCase):
    """Tests for text cleaning."""

    @classmethod
    def setUpClass(cls):
        item1_path = SEC_FIXTURES / "apple_10k_item1_business.json"
        if not item1_path.exists():
            raise unittest.SkipTest("Item 1 fixture not available")

        with open(item1_path) as f:
            data = json.load(f)
            cls.sample_text = data["item1_business_text"]

    def test_preserves_content(self):
        result = clean_extracted_text(self.sample_text)

        assert "Company Background" in result
        assert "iPhone" in result
        assert "Services" in result

    def test_removes_standalone_page_numbers(self):
        text_with_page_numbers = "Some content\n\n42\n\nMore content\n\n17\n\nEnd"
        result = clean_extracted_text(text_with_page_numbers)

        assert "42" not in result
        assert "17" not in result
        assert "Some content" in result
        assert "More content" in result

    def test_normalizes_excessive_newlines(self):
        text_with_many_newlines = "First paragraph\n\n\n\n\n\nSecond paragraph"
        result = clean_extracted_text(text_with_many_newlines)

        assert "\n\n\n" not in result
        assert "First paragraph" in result
        assert "Second paragraph" in result

    def test_strips_whitespace(self):
        text_with_whitespace = "   \n\nContent here\n\n   "
        result = clean_extracted_text(text_with_whitespace)

        assert result == "Content here"

    def test_removes_sec_boilerplate(self):
        text_with_boilerplate = "Apple Inc. | 2025 Form 10-K | 1\nActual content here"
        result = clean_extracted_text(text_with_boilerplate)

        assert "| 2025 Form 10-K |" not in result
        assert "Actual content here" in result
