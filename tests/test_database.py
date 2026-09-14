"""
ReviewLens SQLite Database and History Endpoints Unit Tests
===========================================================
Verifies SQLite persistence, zero-dummy initial state, CRUD operations,
and /api/v1/history and /api/v1/history/stats endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from backend.database import (
    clear_all_reviews,
    delete_saved_review,
    get_history_stats,
    get_saved_reviews,
    init_db,
    save_review,
)
from backend.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    """Ensure clean database before and after each test."""
    init_db(clear_dummy=True)
    clear_all_reviews()
    yield
    clear_all_reviews()


class TestDatabaseOperations:
    """Test suite for direct SQLite database operations."""

    def test_init_db_has_zero_dummy_records(self):
        """Verify that newly initialized database contains zero dummy records."""
        stats = get_history_stats()
        assert stats["total_reviews"] == 0
        assert stats["text_count"] == 0
        assert stats["url_count"] == 0

    def test_save_and_retrieve_text_review(self):
        """Verify saving and retrieving a single text review."""
        saved = save_review(
            review_text="Outstanding display and great ergonomics.",
            sentiment_label="Positive",
            sentiment_strength="Strong Positive",
            compound_score=0.85,
            vader_pos=0.45,
            vader_neu=0.55,
            vader_neg=0.0,
            source_type="text",
        )
        assert saved["id"] > 0
        assert saved["sentiment_label"] == "Positive"

        history = get_saved_reviews()
        assert history["total"] == 1
        first = history["reviews"][0]
        assert first["id"] == saved["id"]
        assert first["review_text"] == "Outstanding display and great ergonomics."

    def test_delete_saved_review(self):
        """Verify deleting a specific saved review."""
        saved = save_review(
            review_text="Mediocre product, broke quickly.",
            sentiment_label="Negative",
            sentiment_strength="Strong Negative",
            compound_score=-0.65,
            vader_pos=0.0,
            vader_neu=0.4,
            vader_neg=0.6,
            source_type="text",
        )
        deleted = delete_saved_review(saved["id"])
        assert deleted is True

        history = get_saved_reviews()
        assert history["total"] == 0


class TestHistoryApiEndpoints:
    """Test suite for /api/v1/history REST endpoints."""

    def test_text_analysis_auto_persists_to_history(self):
        """Verify that POST /api/v1/analyze/text automatically saves to SQLite."""
        payload = {"text": "I really love this smartphone, it works like a charm!"}
        res = client.post("/api/v1/analyze/text", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert "saved_id" in data
        assert data["saved_id"] is not None

        # Query history
        hist_res = client.get("/api/v1/history")
        assert hist_res.status_code == 200
        hist_data = hist_res.json()
        assert hist_data["total"] == 1
        assert hist_data["reviews"][0]["id"] == data["saved_id"]

    def test_history_stats_endpoint(self):
        """Verify GET /api/v1/history/stats returns correct counts."""
        client.post("/api/v1/analyze/text", json={"text": "Super fast and reliable."})
        res = client.get("/api/v1/history/stats")
        assert res.status_code == 200
        stats = res.json()
        assert stats["total_reviews"] == 1
        assert stats["text_count"] == 1
        assert stats["positive_count"] == 1

    def test_delete_history_endpoint(self):
        """Verify DELETE /api/v1/history/{id} removes the review."""
        post_res = client.post("/api/v1/analyze/text", json={"text": "To be removed."})
        saved_id = post_res.json()["saved_id"]

        del_res = client.delete(f"/api/v1/history/{saved_id}")
        assert del_res.status_code == 200

        check_res = client.get("/api/v1/history")
        assert check_res.json()["total"] == 0
