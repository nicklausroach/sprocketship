"""Shared pytest fixtures and configuration"""

import pytest
from pathlib import Path


@pytest.fixture
def fixtures_path():
    """Return the path to test fixtures directory"""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_config():
    """Sample configuration dictionary for testing"""
    return {
        "snowflake": {
            "account": "test_account",
            "user": "test_user",
            "password": "test_password",
            "role": "sysadmin",
            "warehouse": "test_warehouse",
        },
        "procedures": {
            "+database": "default_db",
            "+schema": "default_schema",
            "+language": "javascript",
            "+execute_as": "owner",
        },
    }
