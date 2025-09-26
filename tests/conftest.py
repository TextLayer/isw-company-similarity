import json
import os
import sys
from unittest.mock import Mock

import pytest

# Add the parent directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


def _load_recruitment_fixture_data():
    """Load recruitment fixture data from JSON file"""
    fixture_path = os.path.join(
        os.path.dirname(__file__),
        "fixtures",
        "applications",
        "application.json"
    )
    with open(fixture_path, 'r') as f:
        return json.load(f)


@pytest.fixture
def mock_ashby_application_data():
    """Mock Ashby application data for testing"""
    data = _load_recruitment_fixture_data()
    return data["application"]


@pytest.fixture
def mock_ashby_candidate_data():
    """Mock Ashby candidate data for testing"""
    data = _load_recruitment_fixture_data()
    return data["candidate"]


@pytest.fixture
def mock_job_document_data():
    """Mock job document data for testing"""
    data = _load_recruitment_fixture_data()
    return data["job"]


@pytest.fixture
def test_application_id():
    """Test application ID"""
    data = _load_recruitment_fixture_data()
    return data["ids"]["application_id"]


@pytest.fixture
def test_candidate_id():
    """Test candidate ID"""
    data = _load_recruitment_fixture_data()
    return data["ids"]["candidate_id"]


@pytest.fixture
def mock_executor():
    """Mock executor for testing controllers without executing real commands"""
    from isw.core.commands.executor import Executor

    mock = Mock(spec=Executor)
    mock.execute_read = Mock(return_value={"status": "success"})
    mock.execute_write = Mock(return_value={"status": "created"})
    return mock


@pytest.fixture
def test_config():
    """Fixture for test configuration"""
    return {"TESTING": True, "DEBUG": False, "SECRET_KEY": "test-secret-key", "FLASK_CONFIG": "TEST"}


@pytest.fixture
def auth_headers():
    """Fixture for authenticated request headers"""
    return {"Authorization": "Bearer test-token", "Content-Type": "application/json"}


@pytest.fixture
def sample_user():
    """Fixture for a sample user object"""
    return {"id": "test-user-123", "email": "test@example.com", "name": "Test User", "role": "user"}


# Configure pytest to ignore deprecation warnings from libraries
def pytest_configure(config):
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "unit: mark test as a unit test")
