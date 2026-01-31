"""Unit tests for entity service configuration."""

import dataclasses

import pytest

from isw.core.services.entities.config import (
    DescriptionTagConfig,
    EntityServiceConfig,
    RevenueTagConfig,
)


class TestRevenueTagConfig:
    """Tests for revenue tag configuration."""

    def test_default_has_sec_tags(self):
        """Default config should have SEC revenue tags."""
        config = RevenueTagConfig()
        assert len(config.sec_tags) > 0
        assert "us-gaap:Revenues" in config.sec_tags

    def test_default_has_ifrs_tags(self):
        """Default config should have IFRS revenue tags."""
        config = RevenueTagConfig()
        assert len(config.ifrs_tags) > 0
        assert "ifrs-full:Revenue" in config.ifrs_tags

    def test_default_currencies(self):
        """Default config should support major currencies."""
        config = RevenueTagConfig()
        assert "USD" in config.supported_currencies
        assert "GBP" in config.supported_currencies
        assert "EUR" in config.supported_currencies

    def test_immutable(self):
        """Config should be frozen (immutable)."""
        config = RevenueTagConfig()
        with pytest.raises(dataclasses.FrozenInstanceError):
            config.sec_tags = ("custom:tag",)


class TestDescriptionTagConfig:
    """Tests for description tag configuration."""

    def test_default_has_ifrs_tags(self):
        """Default config should have IFRS description tags."""
        config = DescriptionTagConfig()
        assert len(config.ifrs_tags) > 0
        # Check for the main description tag
        assert any("DescriptionOfNature" in tag for tag in config.ifrs_tags)

    def test_tag_field_names_mapping(self):
        """Tag field names should map tags to readable names."""
        config = DescriptionTagConfig()
        assert len(config.tag_field_names) > 0
        # Check a specific mapping
        for _tag, name in config.tag_field_names.items():
            assert isinstance(name, str)
            assert "_" in name or name.islower()  # Should be snake_case


class TestEntityServiceConfig:
    """Tests for main service configuration."""

    def test_default_values(self):
        """Default config should have sensible defaults."""
        config = EntityServiceConfig()
        assert config.timeout == 30.0
        assert config.use_ai_extraction is True
        assert config.use_web_search_fallback is True
        assert config.llm_model == "gpt-4o-mini"

    def test_default_sec_user_agent(self):
        """Default config should have a placeholder user agent."""
        config = EntityServiceConfig()
        assert "@" in config.sec_user_agent  # Should have email format

    def test_custom_values(self):
        """Config should accept custom values."""
        config = EntityServiceConfig(
            sec_user_agent="My App admin@example.com",
            timeout=60.0,
            use_ai_extraction=False,
        )
        assert config.sec_user_agent == "My App admin@example.com"
        assert config.timeout == 60.0
        assert config.use_ai_extraction is False

    def test_nested_configs(self):
        """Config should have nested tag configurations."""
        config = EntityServiceConfig()
        assert isinstance(config.revenue_tags, RevenueTagConfig)
        assert isinstance(config.description_tags, DescriptionTagConfig)

    def test_web_search_backend_validation(self):
        """Web search backend should be one of allowed values."""
        config = EntityServiceConfig(web_search_backend="perplexity")
        assert config.web_search_backend == "perplexity"

        config = EntityServiceConfig(web_search_backend="firecrawl")
        assert config.web_search_backend == "firecrawl"
