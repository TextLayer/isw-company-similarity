"""Shared fixtures for entities integration tests."""

import json
from pathlib import Path

import pytest

# Fixture directories
FIXTURES_DIR = Path(__file__).parent.parent.parent.parent.parent / "fixtures"
REGISTRY_FIXTURES = FIXTURES_DIR / "entity_registry"
STORAGE_FIXTURES = FIXTURES_DIR / "entity_storage"


@pytest.fixture
def sec_apple_submission() -> dict:
    """Load Apple SEC submission fixture."""
    with open(REGISTRY_FIXTURES / "sec_data" / "apple_submission.json") as f:
        return json.load(f)


@pytest.fixture
def sec_microsoft_submission() -> dict:
    """Load Microsoft SEC submission fixture."""
    with open(REGISTRY_FIXTURES / "sec_data" / "microsoft_submission.json") as f:
        return json.load(f)


@pytest.fixture
def sec_tesla_submission() -> dict:
    """Load Tesla SEC submission fixture."""
    with open(REGISTRY_FIXTURES / "sec_data" / "tesla_submission.json") as f:
        return json.load(f)


@pytest.fixture
def esef_gb_filings() -> dict:
    """Load GB ESEF filings fixture."""
    with open(REGISTRY_FIXTURES / "esef_data" / "gb_filings.json") as f:
        return json.load(f)


@pytest.fixture
def esef_fr_filings() -> dict:
    """Load FR ESEF filings fixture."""
    with open(REGISTRY_FIXTURES / "esef_data" / "fr_filings.json") as f:
        return json.load(f)


@pytest.fixture
def esef_mixed_filings() -> dict:
    """Load mixed jurisdiction ESEF filings fixture."""
    with open(REGISTRY_FIXTURES / "esef_data" / "mixed_filings.json") as f:
        return json.load(f)


@pytest.fixture
def kainos_xbrl_json() -> dict:
    """Load Kainos XBRL-JSON fixture for revenue extraction."""
    with open(STORAGE_FIXTURES / "xbrl_json" / "kainos_2022.json") as f:
        return json.load(f)


@pytest.fixture
def mlsystem_xbrl_json() -> dict:
    """Load MLSystem XBRL-JSON fixture (multi-field example)."""
    with open(STORAGE_FIXTURES / "xbrl_json" / "mlsystem_multi_field.json") as f:
        return json.load(f)


@pytest.fixture
def apple_10k_html() -> str:
    """Load Apple 10-K HTML excerpt fixture."""
    with open(STORAGE_FIXTURES / "sec_data" / "apple_10k_2025.htm") as f:
        return f.read()


@pytest.fixture
def apple_company_facts() -> dict:
    """Load Apple company facts fixture."""
    with open(STORAGE_FIXTURES / "sec_data" / "apple_company_facts.json") as f:
        return json.load(f)


@pytest.fixture
def apple_10k_item1_business() -> dict:
    """Load Apple 10-K Item 1 Business fixture."""
    with open(STORAGE_FIXTURES / "sec_data" / "apple_10k_item1_business.json") as f:
        return json.load(f)
