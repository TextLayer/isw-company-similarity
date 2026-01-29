"""Unit tests for BaseDataSource and related data classes."""

import unittest

from isw.core.services.data_sources.base import (
    BaseDataSource,
    BusinessDescription,
    DataSourceError,
    Filing,
    FilingNotFoundError,
    RateLimitError,
    RevenueData,
)


class ConcreteDataSource(BaseDataSource):
    """Concrete implementation for testing."""

    @property
    def source_name(self) -> str:
        return "Test Source"

    def get_filing(self, identifier: str, filing_type: str) -> Filing | None:
        return None

    def get_latest_annual_filing(self, identifier: str) -> Filing | None:
        return None

    def get_business_description(self, identifier: str) -> BusinessDescription | None:
        return None

    def get_revenue(self, identifier: str) -> RevenueData | None:
        return None

    def list_filings(self, identifier: str, filing_type: str | None = None, limit: int = 10) -> list[Filing]:
        return []


class TestFiling(unittest.TestCase):
    def test_creates_filing_with_required_fields(self):
        filing = Filing(
            identifier="0000320193",
            filing_type="10-K",
            filing_date="2024-10-31",
        )

        assert filing.identifier == "0000320193"
        assert filing.filing_type == "10-K"
        assert filing.filing_date == "2024-10-31"
        assert filing.accession_number is None
        assert filing.document_url is None

    def test_creates_filing_with_all_fields(self):
        filing = Filing(
            identifier="0000320193",
            filing_type="10-K",
            filing_date="2024-10-31",
            accession_number="0000320193-24-000123",
            document_url="https://sec.gov/...",
            raw_data={"key": "value"},
        )

        assert filing.accession_number == "0000320193-24-000123"
        assert filing.document_url == "https://sec.gov/..."
        assert filing.raw_data == {"key": "value"}


class TestBusinessDescription(unittest.TestCase):
    def test_creates_business_description(self):
        desc = BusinessDescription(
            text="Apple designs, manufactures...",
            source_filing="10-K",
            extraction_method="html_parse",
        )

        assert desc.text == "Apple designs, manufactures..."
        assert desc.source_filing == "10-K"
        assert desc.extraction_method == "html_parse"


class TestRevenueData(unittest.TestCase):
    def test_creates_revenue_data(self):
        revenue = RevenueData(
            amount=394328000000,
            currency="USD",
            period_end="2024-09-28",
            source_tag="us-gaap:Revenues",
        )

        assert revenue.amount == 394328000000
        assert revenue.currency == "USD"
        assert revenue.period_end == "2024-09-28"
        assert revenue.source_tag == "us-gaap:Revenues"


class TestExceptions(unittest.TestCase):
    def test_data_source_error_is_exception(self):
        assert issubclass(DataSourceError, Exception)

    def test_filing_not_found_is_data_source_error(self):
        assert issubclass(FilingNotFoundError, DataSourceError)

    def test_rate_limit_is_data_source_error(self):
        assert issubclass(RateLimitError, DataSourceError)

    def test_can_raise_and_catch_errors(self):
        with self.assertRaises(DataSourceError):
            raise FilingNotFoundError("Not found")

        with self.assertRaises(DataSourceError):
            raise RateLimitError("Rate limited")


class TestBaseDataSource(unittest.TestCase):
    def test_cannot_instantiate_abstract_class(self):
        with self.assertRaises(TypeError):
            BaseDataSource()

    def test_concrete_implementation_has_source_name(self):
        source = ConcreteDataSource()
        assert source.source_name == "Test Source"

    def test_supports_identifier_returns_true_by_default(self):
        source = ConcreteDataSource()
        assert source.supports_identifier("any-identifier") is True

    def test_concrete_methods_are_callable(self):
        source = ConcreteDataSource()

        assert source.get_filing("123", "10-K") is None
        assert source.get_latest_annual_filing("123") is None
        assert source.get_business_description("123") is None
        assert source.get_revenue("123") is None
        assert source.list_filings("123") == []
