"""
ReviewLens Analytics and URL Analysis Endpoint Tests
====================================================
Verifies /api/v1/analytics/products, /api/v1/analytics/categories,
strict JSON serializability (no unhandled NaNs), and controlled scraping behavior
when ENABLE_PLAYWRIGHT_SCRAPING is disabled or URLs are unsafe.
"""

import json
import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


class TestApiAnalyticsAndScraping:
    """Test suite for analytics endpoints and controlled scraping behavior."""

    def test_product_analytics_endpoint(self):
        """Verify GET /api/v1/analytics/products returns list of valid product metrics."""
        response = client.get("/api/v1/analytics/products")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        first = data[0]
        assert "product_name" in first
        assert "product_category" in first
        assert "review_count" in first
        assert "average_rating" in first
        assert "average_compound_score" in first
        assert "positive_percentage" in first
        assert "negative_percentage" in first
        assert "average_word_count" in first

        # Ensure sorting: review_count descending
        counts = [p["review_count"] for p in data]
        assert counts == sorted(counts, reverse=True)

    def test_category_analytics_endpoint(self):
        """Verify GET /api/v1/analytics/categories returns list of valid category metrics."""
        response = client.get("/api/v1/analytics/categories")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        first = data[0]
        assert "product_category" in first
        assert "review_count" in first
        assert "average_rating" in first
        assert "average_compound_score" in first
        assert "positive_percentage" in first
        assert "negative_percentage" in first

        # Ensure sorting: review_count descending
        counts = [c["review_count"] for c in data]
        assert counts == sorted(counts, reverse=True)

    def test_json_serializability_and_no_nan_leak(self):
        """Verify analytics and demo responses can be re-serialized without NaN errors."""
        endpoints = [
            "/api/v1/info",
            "/api/v1/demo/summary",
            "/api/v1/demo/reviews?limit=50",
            "/api/v1/analytics/products",
            "/api/v1/analytics/categories",
        ]
        for ep in endpoints:
            res = client.get(ep)
            assert res.status_code == 200
            # Ensure text does not contain bare JavaScript NaN literals
            raw_text = res.text
            assert "NaN" not in raw_text, f"Endpoint {ep} emitted unhandled NaN token!"
            # Ensure roundtrip JSON serialization succeeds
            data = res.json()
            serialized = json.dumps(data)
            assert isinstance(serialized, str)

    def test_url_analysis_success_and_saves_to_db(self):
        """Verify that URL analysis successfully extracts reviews and saves to SQLite."""
        payload = {
            "url": "https://example.com/product/123",
            "max_reviews": 5,
        }
        response = client.post("/api/v1/analyze/url", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert data["total"] > 0
        assert len(data["reviews"]) > 0
        assert data["saved_to_db"] is True

    def test_url_scraping_unsafe_url_returns_400(self):
        """Verify that an SSRF / private IP target returns HTTP 400."""
        payload = {
            "url": "http://127.0.0.1:8000/internal",
            "max_reviews": 5,
        }
        response = client.post("/api/v1/analyze/url", json=payload)
        # Rejection happens during schema validation or URL validation
        assert response.status_code in {400, 422}
        data = response.json()
        assert data["status"] == "error"

    def test_url_scraping_localhost_returns_error(self):
        """Verify that localhost returns HTTP 400 / 422."""
        payload = {
            "url": "http://localhost:8000/test",
            "max_reviews": 5,
        }
        response = client.post("/api/v1/analyze/url", json=payload)
        assert response.status_code in {400, 422}
        data = response.json()
        assert data["status"] == "error"
