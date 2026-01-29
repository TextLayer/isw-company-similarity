"""Fixtures for entity collection tests."""

import json
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent


def load_fixture(name: str) -> dict:
    """Load a JSON fixture file."""
    path = FIXTURES_DIR / name
    with open(path) as f:
        return json.load(f)
