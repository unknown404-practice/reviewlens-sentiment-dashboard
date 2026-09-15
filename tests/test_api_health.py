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

    def test_cors_allowed_for_all_vercel_subdomains(self):
        """Verify that any Vercel deployment hash or preview subdomain is allowed by CORS."""
        test_origins = [
            "https://reviewlens-sentiment-dashboard.vercel.app",
            "https://reviewlens-sentiment-dashboard-dflx0ip3h-noteam02com.vercel.app",
            "https://reviewlens-sentiment-dashboard-git-main-noteam02com.vercel.app",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]
        for origin in test_origins:
            response = client.get("/health", headers={"Origin": origin})
            assert response.status_code == 200
            assert response.headers.get("access-control-allow-origin") == origin, (
                f"Failed to allow origin: {origin}"
            )

    def test_cors_preflight_options_request(self):
        """Verify CORS preflight OPTIONS request returns 200 and allowed methods."""
        preview_origin = "https://reviewlens-sentiment-dashboard-dflx0ip3h-noteam02com.vercel.app"
        response = client.options(
            "/api/v1/analyze/text",
            headers={
                "Origin": preview_origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            },
        )
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == preview_origin
        assert "POST" in response.headers.get("access-control-allow-methods", "")
