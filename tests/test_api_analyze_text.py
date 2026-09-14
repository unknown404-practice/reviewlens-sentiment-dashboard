"""
ReviewLens Text Analysis Endpoint Tests
=======================================
Verifies POST /api/v1/analyze/text for positive/negative scoring,
whitespace validation rejection, length boundary enforcement, and response model structure.
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


class TestApiAnalyzeText:
    """Test suite for VADER text sentiment scoring endpoint."""

    def test_positive_text_analysis(self):
        """Test scoring of an unambiguously positive review."""
        payload = {"text": "Excellent quality, fast delivery, and I absolutely love it."}
        response = client.post("/api/v1/analyze/text", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert data["text"] == payload["text"]
        assert data["sentiment_label"] == "Positive"
        assert data["sentiment_strength"] in {"Positive", "Strong Positive"}

        scores = data["scores"]
        assert scores["pos"] > 0.0
        assert scores["compound"] >= 0.05
        assert isinstance(scores["neg"], float)
        assert isinstance(scores["neu"], float)

    def test_negative_text_analysis(self):
        """Test scoring of an unambiguously negative review."""
        payload = {"text": "Terrible product. It broke immediately and customer service refused to help."}
        response = client.post("/api/v1/analyze/text", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert data["sentiment_label"] == "Negative"
        assert data["sentiment_strength"] in {"Negative", "Strong Negative"}

        scores = data["scores"]
        assert scores["neg"] > 0.0
        assert scores["compound"] <= -0.05

    def test_whitespace_only_validation_failure(self):
        """Test that whitespace-only input returns 422 validation failure."""
        payload = {"text": "     \n\t   "}
        response = client.post("/api/v1/analyze/text", json=payload)
        assert response.status_code == 422

        data = response.json()
        assert data["status"] == "error"
        assert "cannot be empty or whitespace-only" in data["detail"]

    def test_empty_string_validation_failure(self):
        """Test that empty string returns 422 validation failure."""
        payload = {"text": ""}
        response = client.post("/api/v1/analyze/text", json=payload)
        assert response.status_code == 422

        data = response.json()
        assert data["status"] == "error"

    def test_overly_long_text_validation_failure(self):
        """Test that text exceeding 5000 characters is rejected with 422."""
        huge_text = "Good " * 1100  # > 5500 characters
        payload = {"text": huge_text}
        response = client.post("/api/v1/analyze/text", json=payload)
        assert response.status_code == 422

        data = response.json()
        assert data["status"] == "error"
        assert "exceeds maximum allowed length" in data["detail"]
