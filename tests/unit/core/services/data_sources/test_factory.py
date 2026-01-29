import unittest

from isw.core.services.data_sources import DataSourceError
from isw.core.services.data_sources.edgar_data_source import SECEdgarDataSource
from isw.core.services.data_sources.esef_data_source import FilingsXBRLDataSource
from isw.core.services.data_sources.factory import DataSourceFactory


class TestDataSourceFactory(unittest.TestCase):
    def setUp(self):
        self.factory = DataSourceFactory(sec_user_agent="Test test@example.com")

    def test_has_two_sources(self):
        assert len(self.factory.sources) == 2

    def test_sources_include_sec_edgar(self):
        source_types = [type(s) for s in self.factory.sources]
        assert SECEdgarDataSource in source_types

    def test_sources_include_esef(self):
        source_types = [type(s) for s in self.factory.sources]
        assert FilingsXBRLDataSource in source_types


class TestGetSourceForIdentifier(unittest.TestCase):
    def setUp(self):
        self.factory = DataSourceFactory(sec_user_agent="Test test@example.com")

    def test_routes_cik_to_sec_edgar(self):
        source = self.factory.get_source_for_identifier("0000320193")
        assert isinstance(source, SECEdgarDataSource)

    def test_routes_short_cik_to_sec_edgar(self):
        source = self.factory.get_source_for_identifier("320193")
        assert isinstance(source, SECEdgarDataSource)

    def test_routes_lei_to_esef(self):
        source = self.factory.get_source_for_identifier("213800H2PQMIF3OVZY47")
        assert isinstance(source, FilingsXBRLDataSource)

    def test_returns_none_for_invalid_identifier(self):
        source = self.factory.get_source_for_identifier("invalid-id-format")
        assert source is None

    def test_returns_none_for_empty_identifier(self):
        source = self.factory.get_source_for_identifier("")
        assert source is None


class TestFactoryMethodsRaiseOnInvalidIdentifier(unittest.TestCase):
    def setUp(self):
        self.factory = DataSourceFactory(sec_user_agent="Test test@example.com")

    def test_get_filing_raises_for_invalid_identifier(self):
        with self.assertRaises(DataSourceError) as ctx:
            self.factory.get_filing("invalid-id", "10-K")
        assert "No data source supports identifier" in str(ctx.exception)

    def test_get_latest_annual_filing_raises_for_invalid_identifier(self):
        with self.assertRaises(DataSourceError) as ctx:
            self.factory.get_latest_annual_filing("invalid-id")
        assert "No data source supports identifier" in str(ctx.exception)

    def test_get_business_description_raises_for_invalid_identifier(self):
        with self.assertRaises(DataSourceError) as ctx:
            self.factory.get_business_description("invalid-id")
        assert "No data source supports identifier" in str(ctx.exception)

    def test_get_revenue_raises_for_invalid_identifier(self):
        with self.assertRaises(DataSourceError) as ctx:
            self.factory.get_revenue("invalid-id")
        assert "No data source supports identifier" in str(ctx.exception)

    def test_list_filings_raises_for_invalid_identifier(self):
        with self.assertRaises(DataSourceError) as ctx:
            self.factory.list_filings("invalid-id")
        assert "No data source supports identifier" in str(ctx.exception)


class TestFactoryConfiguration(unittest.TestCase):
    def test_custom_timeout(self):
        factory = DataSourceFactory(sec_user_agent="Test test@example.com", timeout=60.0)
        # Verify the timeout is passed through
        assert factory._sec_source.timeout == 60.0
        assert factory._esef_source.timeout == 60.0

    def test_default_timeout(self):
        factory = DataSourceFactory(sec_user_agent="Test test@example.com")
        assert factory._sec_source.timeout == 30.0
        assert factory._esef_source.timeout == 30.0
