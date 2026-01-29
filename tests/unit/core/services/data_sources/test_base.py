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
    def test_creates_sec_filing(self):
        filing = Filing(
            identifier="0000320193",
            filing_type="10-K",
            period_end="2024-09-28",
            filed_at="2024-10-31",
            accession_number="0000320193-24-000123",
            document_url="https://sec.gov/Archives/edgar/data/320193/...",
        )

        assert filing.identifier == "0000320193"
        assert filing.filing_type == "10-K"
        assert filing.period_end == "2024-09-28"
        assert filing.filed_at == "2024-10-31"
        assert filing.accession_number == "0000320193-24-000123"

    def test_creates_esef_filing(self):
        filing = Filing(
            identifier="213800H2PQMIF3OVZY47",
            filing_type="AFR",
            period_end="2022-03-31",
            document_url="/213800H2PQMIF3OVZY47/2022-03-31/ESEF/GB/0/report.xhtml",
        )

        assert filing.identifier == "213800H2PQMIF3OVZY47"
        assert filing.filing_type == "AFR"
        assert filing.period_end == "2022-03-31"
        assert filing.filed_at is None
        assert filing.accession_number is None

    def test_filing_with_raw_data(self):
        filing = Filing(
            identifier="0000320193",
            filing_type="10-K",
            period_end="2024-09-28",
            raw_data={"form": "10-K", "size": 15000000},
        )

        assert filing.raw_data == {"form": "10-K", "size": 15000000}


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
