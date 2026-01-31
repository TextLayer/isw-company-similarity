"""Integration tests for EntityService.

These tests verify end-to-end workflows using the EntityService facade.
"""

import pytest

from isw.core.services.entities import (
    CIK,
    LEI,
    EntityError,
    EntityService,
    EntityServiceConfig,
)


class TestEntityServiceIdentifierRouting:
    """Test that EntityService routes to correct adapter based on identifier."""

    @pytest.fixture
    def service(self):
        """Create service with default config."""
        config = EntityServiceConfig(
            use_ai_extraction=False,  # Disable AI for tests
            use_web_search_fallback=False,
        )
        return EntityService(config=config)

    def test_parse_cik_identifier(self, service):
        """Should correctly parse CIK identifiers."""
        identifier = service._parse_identifier("320193")
        assert isinstance(identifier, CIK)
        assert identifier.value == "0000320193"

    def test_parse_lei_identifier(self, service):
        """Should correctly parse LEI identifiers."""
        identifier = service._parse_identifier("213800H2PQMIF3OVZY47")
        assert isinstance(identifier, LEI)
        assert identifier.value == "213800H2PQMIF3OVZY47"

    def test_parse_invalid_identifier_raises(self, service):
        """Should raise EntityError for invalid identifiers."""
        with pytest.raises(EntityError, match="Invalid identifier"):
            service._parse_identifier("not-valid")


class TestEntityServiceConfig:
    """Test EntityService configuration."""

    def test_custom_config(self):
        """Should accept custom configuration."""
        config = EntityServiceConfig(
            sec_user_agent="Test App test@example.com",
            timeout=60.0,
            use_ai_extraction=True,
            use_web_search_fallback=False,
        )
        service = EntityService(config=config)

        assert service._config.sec_user_agent == "Test App test@example.com"
        assert service._config.timeout == 60.0
        assert service._config.use_ai_extraction is True
        assert service._config.use_web_search_fallback is False

    def test_default_config(self):
        """Should use defaults when no config provided."""
        service = EntityService()

        assert service._config is not None
        assert service._config.timeout == 30.0


class TestEntityServiceLazyInit:
    """Test that components are initialized lazily."""

    def test_adapters_not_created_immediately(self):
        """Adapters should not be created until needed."""
        service = EntityService()

        assert service._edgar_adapter is None
        assert service._esef_adapter is None

    def test_registries_not_created_immediately(self):
        """Registries should not be created until needed."""
        service = EntityService()

        assert service._edgar_registry is None
        assert service._esef_registry is None

    def test_extractors_not_created_immediately(self):
        """Extractors should not be created until needed."""
        service = EntityService()

        assert service._revenue_extractor is None
        assert service._description_extractor is None


class TestEntityServiceAnnualFilingDetection:
    """Test annual filing detection logic."""

    @pytest.fixture
    def service(self):
        return EntityService()

    def test_december_year_end_is_annual(self, service):
        """December 31 filings should be detected as annual."""
        from isw.core.services.entities import Filing

        filing = Filing(
            identifier="TEST123",
            filing_type="AFR",
            period_end="2022-12-31",
        )
        assert service._is_annual_filing(filing) is True

    def test_december_28_plus_is_annual(self, service):
        """December 28-31 filings should be detected as annual."""
        from isw.core.services.entities import Filing

        filing = Filing(
            identifier="TEST123",
            filing_type="AFR",
            period_end="2022-12-28",
        )
        assert service._is_annual_filing(filing) is True

    def test_june_30_is_likely_half_year(self, service):
        """June 30 filings are likely half-year reports."""
        from isw.core.services.entities import Filing

        filing = Filing(
            identifier="TEST123",
            filing_type="AFR",
            period_end="2022-06-30",
        )
        assert service._is_annual_filing(filing) is False

    def test_missing_period_defaults_to_false(self, service):
        """Filings without period_end should not be considered annual."""
        from isw.core.services.entities import Filing

        filing = Filing(
            identifier="TEST123",
            filing_type="AFR",
            period_end="",
        )
        assert service._is_annual_filing(filing) is False

    def test_march_year_end_is_annual(self, service):
        """Non-calendar year ends should also be detected as annual."""
        from isw.core.services.entities import Filing

        filing = Filing(
            identifier="TEST123",
            filing_type="AFR",
            period_end="2022-03-31",
        )
        # March 31 is a common fiscal year end (e.g., UK companies)
        # Our heuristic defaults to True for non-June-30 dates
        assert service._is_annual_filing(filing) is True


class TestEntityServiceDependencyInjection:
    """Test that custom components can be injected."""

    def test_inject_custom_revenue_extractor(self):
        """Should use injected revenue extractor."""
        from isw.core.services.entities.extractors import RevenueExtractor

        custom_extractor = RevenueExtractor(sec_tags=["custom:Tag"])
        service = EntityService(revenue_extractor=custom_extractor)

        assert service._get_revenue_extractor() is custom_extractor
        assert service._get_revenue_extractor().sec_tags == ["custom:Tag"]

    def test_inject_custom_adapter(self):
        """Should use injected adapters."""
        from isw.core.services.entities.storage import EdgarAdapter

        custom_adapter = EdgarAdapter(user_agent="Custom Agent custom@test.com")
        service = EntityService(edgar_adapter=custom_adapter)

        assert service._get_edgar_adapter() is custom_adapter
