"""
Global pytest configuration and fixtures for ReviewLens.
Guarantees that the SQLite schema and test environment are clean and initialized.
"""

import pytest
from backend.database import init_db, clear_all_reviews


@pytest.fixture(autouse=True, scope="session")
def setup_test_database():
    """Ensure database schema is created on fresh CI environments before any tests run."""
    init_db(clear_dummy=True)
