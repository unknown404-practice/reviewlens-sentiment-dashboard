"""
ReviewLens System & Health API Tests
====================================
Verifies root welcome endpoint and /health status endpoint responses and schemas.
"""

import pytest
from fastapi.testclient import TestClient

from backend.config import get_settings
from backend.main import app

client = TestClient(app)


class TestApiHealth:
    """Test suite for system root and health endpoints."""

    def test_root_endpoint(self):
        """Test GET / returns 200 and valid schema fields."""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert "Welcome to ReviewLens Sentiment API" in data["message"]
        assert data["docs_url"] == "/docs"
        assert data["health_url"] == "/health"
        assert data["api_version"] == "v1"

    def test_health_endpoint(self):
        """Test GET /health returns 200, service metadata, and healthy status."""
        settings = get_settings()
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == settings.APP_NAME
        assert data["version"] == settings.APP_VERSION
        assert data["environment"] == settings.ENVIRONMENT
