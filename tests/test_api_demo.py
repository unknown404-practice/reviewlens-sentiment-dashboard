"""
ReviewLens Demo Data & Browsing Endpoint Tests
==============================================
Verifies /api/v1/info, /api/v1/demo/summary, /api/v1/demo/reviews (with pagination and filtering),
and top-reviews endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


class TestApiDemo:
    """Test suite for demo data browsing, filtering, and summary endpoints."""

    def test_info_endpoint(self):
        """Test GET /api/v1/info returns dataset provenance and features."""
        response = client.get("/api/v1/info")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert data["data_mode"] == "DEMO"
        assert "data/processed/reviews_with_sentiment.csv" in data["dataset_path"]
        assert data["total_reviews"] > 0
        assert isinstance(data["source_counts"], dict)
        assert len(data["supported_features"]) > 0
        assert data["scraping_enabled"] is False

    def test_demo_summary_endpoint(self):
        """Test GET /api/v1/demo/summary returns dataset aggregation metrics."""
        response = client.get("/api/v1/demo/summary")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert data["total_reviews"] > 0
        assert data["positive_count"] + data["neutral_count"] + data["negative_count"] == data["total_reviews"]
        assert data["positive_percentage"] >= 0.0
        assert -1.0 <= data["average_compound_score"] <= 1.0
        assert 1.0 <= data["average_rating"] <= 5.0

    def test_demo_reviews_default(self):
        """Test GET /api/v1/demo/reviews with default pagination."""
        response = client.get("/api/v1/demo/reviews")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert data["total"] > 0
        assert data["limit"] == 20
        assert data["offset"] == 0
        assert len(data["reviews"]) <= 20
        assert len(data["reviews"]) > 0

        # Validate schema of first review
        first = data["reviews"][0]
        assert "review_id" in first
        assert "product_name" in first
        assert "product_category" in first
        assert "sentiment_label" in first
        assert "compound_score" in first

    def test_demo_reviews_pagination(self):
        """Test pagination limit and offset parameters."""
        res1 = client.get("/api/v1/demo/reviews?limit=5&offset=0")
        assert res1.status_code == 200
        data1 = res1.json()
        assert len(data1["reviews"]) == 5

        res2 = client.get("/api/v1/demo/reviews?limit=5&offset=5")
        assert res2.status_code == 200
        data2 = res2.json()
        assert len(data2["reviews"]) == 5

        # Check that page 1 and page 2 review IDs do not overlap
        ids1 = {r["review_id"] for r in data1["reviews"]}
        ids2 = {r["review_id"] for r in data2["reviews"]}
        assert ids1.isdisjoint(ids2)

    def test_demo_reviews_sentiment_filter(self):
        """Test filtering reviews by sentiment label."""
        response = client.get("/api/v1/demo/reviews?sentiment=Positive&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert all(r["sentiment_label"] == "Positive" for r in data["reviews"])

        neg_response = client.get("/api/v1/demo/reviews?sentiment=Negative&limit=10")
        assert neg_response.status_code == 200
        neg_data = neg_response.json()
        assert all(r["sentiment_label"] == "Negative" for r in neg_data["reviews"])

    def test_demo_reviews_category_filter(self):
        """Test filtering reviews by category."""
        response = client.get("/api/v1/demo/reviews?category=Electronics&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert all(r["product_category"] == "Electronics" for r in data["reviews"])

    def test_no_result_filter_returns_empty_list(self):
        """Test that non-matching filters return 200 OK with empty reviews list."""
        response = client.get("/api/v1/demo/reviews?product=NonExistentProductXYZ123")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["total"] == 0
        assert data["reviews"] == []

    def test_top_positive_reviews(self):
        """Test GET /api/v1/demo/top-reviews/Positive."""
        response = client.get("/api/v1/demo/top-reviews/Positive?limit=5")
        assert response.status_code == 200
        reviews = response.json()
        assert len(reviews) == 5
        assert all(r["sentiment_label"] == "Positive" for r in reviews)
        # Ensure descending compound score
        scores = [r["compound_score"] for r in reviews]
        assert scores == sorted(scores, reverse=True)

    def test_top_negative_reviews(self):
        """Test GET /api/v1/demo/top-reviews/Negative."""
        response = client.get("/api/v1/demo/top-reviews/Negative?limit=5")
        assert response.status_code == 200
        reviews = response.json()
        assert len(reviews) == 5
        assert all(r["sentiment_label"] == "Negative" for r in reviews)
        # Ensure ascending compound score (most negative first)
        scores = [r["compound_score"] for r in reviews]
        assert scores == sorted(scores)

    def test_top_reviews_invalid_sentiment(self):
        """Test that invalid sentiment path parameter is rejected with 400."""
        response = client.get("/api/v1/demo/top-reviews/InvalidSentiment")
        assert response.status_code == 400
        data = response.json()
        assert data["status"] == "error"
        assert "must be 'Positive' or 'Negative'" in data["message"]
