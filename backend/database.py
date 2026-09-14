"""
ReviewLens SQLite Database Layer
================================
Lightweight, zero-dependency persistence layer for user-analyzed text reviews
and URL-extracted reviews. Stores no dummy/synthetic records.
"""

import os
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DB_PATH = os.path.join(DB_DIR, "reviewlens.db")


_SCHEMA_INITIALIZED = False


def _ensure_schema(conn: sqlite3.Connection) -> None:
    global _SCHEMA_INITIALIZED
    if _SCHEMA_INITIALIZED:
        return
    try:
        with conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS saved_reviews (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_type TEXT NOT NULL,
                    source_url TEXT,
                    page_title TEXT,
                    product_name TEXT DEFAULT 'Custom Analysis',
                    product_category TEXT DEFAULT 'General',
                    review_text TEXT NOT NULL,
                    rating REAL,
                    sentiment_label TEXT NOT NULL,
                    sentiment_strength TEXT NOT NULL,
                    compound_score REAL NOT NULL,
                    vader_pos REAL NOT NULL,
                    vader_neu REAL NOT NULL,
                    vader_neg REAL NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_saved_source ON saved_reviews (source_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_saved_sentiment ON saved_reviews (sentiment_label)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_saved_created ON saved_reviews (created_at DESC)")
        _SCHEMA_INITIALIZED = True
    except Exception:
        # Allow retry if schema creation fails
        _SCHEMA_INITIALIZED = False


def get_db_connection() -> sqlite3.Connection:
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=15.0)
    conn.row_factory = sqlite3.Row
    _ensure_schema(conn)
    return conn


def init_db(clear_dummy: bool = True) -> None:
    """Initialize SQLite database schema for ReviewLens reviews."""
    global _SCHEMA_INITIALIZED
    _SCHEMA_INITIALIZED = False
    conn = get_db_connection()
    try:
        with conn:
            if clear_dummy:
                conn.execute("DELETE FROM saved_reviews WHERE source_type = 'dataset'")
    finally:
        conn.close()


def save_review(
    review_text: str,
    sentiment_label: str,
    sentiment_strength: str,
    compound_score: float,
    vader_pos: float,
    vader_neu: float,
    vader_neg: float,
    source_type: str = "text",
    source_url: Optional[str] = None,
    page_title: Optional[str] = None,
    product_name: str = "Custom Analysis",
    product_category: str = "General",
    rating: Optional[float] = None,
    created_at: Optional[str] = None,
) -> Dict[str, Any]:
    """Save a single analyzed review into SQLite."""
    if not created_at:
        created_at = datetime.now(timezone.utc).isoformat()

    conn = get_db_connection()
    try:
        with conn:
            cursor = conn.execute(
                """
                INSERT INTO saved_reviews (
                    source_type, source_url, page_title, product_name, product_category,
                    review_text, rating, sentiment_label, sentiment_strength,
                    compound_score, vader_pos, vader_neu, vader_neg, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    source_type,
                    source_url,
                    page_title,
                    product_name,
                    product_category,
                    review_text.strip(),
                    rating,
                    sentiment_label,
                    sentiment_strength,
                    compound_score,
                    vader_pos,
                    vader_neu,
                    vader_neg,
                    created_at,
                ),
            )
            inserted_id = cursor.lastrowid

        return {
            "id": inserted_id,
            "source_type": source_type,
            "source_url": source_url,
            "page_title": page_title,
            "product_name": product_name,
            "product_category": product_category,
            "review_text": review_text.strip(),
            "rating": rating,
            "sentiment_label": sentiment_label,
            "sentiment_strength": sentiment_strength,
            "compound_score": compound_score,
            "scores": {
                "pos": vader_pos,
                "neu": vader_neu,
                "neg": vader_neg,
                "compound": compound_score,
            },
            "created_at": created_at,
        }
    finally:
        conn.close()


def save_reviews_batch(reviews: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Save multiple reviews in a single SQLite transaction."""
    if not reviews:
        return []

    conn = get_db_connection()
    saved_items = []
    now_iso = datetime.now(timezone.utc).isoformat()
    try:
        with conn:
            for item in reviews:
                created_at = item.get("created_at") or now_iso
                cursor = conn.execute(
                    """
                    INSERT INTO saved_reviews (
                        source_type, source_url, page_title, product_name, product_category,
                        review_text, rating, sentiment_label, sentiment_strength,
                        compound_score, vader_pos, vader_neu, vader_neg, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item.get("source_type", "url"),
                        item.get("source_url"),
                        item.get("page_title"),
                        item.get("product_name", "Extracted Review"),
                        item.get("product_category", "E-Commerce"),
                        item["review_text"].strip(),
                        item.get("rating"),
                        item["sentiment_label"],
                        item["sentiment_strength"],
                        item["compound_score"],
                        item["vader_pos"],
                        item["vader_neu"],
                        item["vader_neg"],
                        created_at,
                    ),
                )
                saved_items.append(
                    {
                        "id": cursor.lastrowid,
                        "source_type": item.get("source_type", "url"),
                        "source_url": item.get("source_url"),
                        "page_title": item.get("page_title"),
                        "product_name": item.get("product_name", "Extracted Review"),
                        "product_category": item.get("product_category", "E-Commerce"),
                        "review_text": item["review_text"].strip(),
                        "rating": item.get("rating"),
                        "sentiment_label": item["sentiment_label"],
                        "sentiment_strength": item["sentiment_strength"],
                        "compound_score": item["compound_score"],
                        "scores": {
                            "pos": item["vader_pos"],
                            "neu": item["vader_neu"],
                            "neg": item["vader_neg"],
                            "compound": item["compound_score"],
                        },
                        "created_at": created_at,
                    }
                )
        return saved_items
    finally:
        conn.close()


def get_saved_reviews(
    source_type: Optional[str] = None,
    sentiment: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> Dict[str, Any]:
    """Retrieve filtered paginated saved reviews."""
    conn = get_db_connection()
    try:
        query = "SELECT * FROM saved_reviews WHERE 1=1"
        count_query = "SELECT COUNT(*) FROM saved_reviews WHERE 1=1"
        params: List[Any] = []

        if source_type and source_type.lower() != "all":
            query += " AND source_type = ?"
            count_query += " AND source_type = ?"
            params.append(source_type.lower())

        if sentiment and sentiment.lower() != "all":
            query += " AND sentiment_label = ?"
            count_query += " AND sentiment_label = ?"
            params.append(sentiment.title())

        if search and search.strip():
            query += " AND (review_text LIKE ? OR product_name LIKE ? OR page_title LIKE ?)"
            count_query += " AND (review_text LIKE ? OR product_name LIKE ? OR page_title LIKE ?)"
            wildcard = f"%{search.strip()}%"
            params.extend([wildcard, wildcard, wildcard])

        total = conn.execute(count_query, params).fetchone()[0]

        query += " ORDER BY id DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor = conn.execute(query, params)
        rows = cursor.fetchall()

        results = []
        for row in rows:
            results.append(
                {
                    "id": row["id"],
                    "source_type": row["source_type"],
                    "source_url": row["source_url"],
                    "page_title": row["page_title"],
                    "product_name": row["product_name"],
                    "product_category": row["product_category"],
                    "review_text": row["review_text"],
                    "rating": row["rating"],
                    "sentiment_label": row["sentiment_label"],
                    "sentiment_strength": row["sentiment_strength"],
                    "compound_score": row["compound_score"],
                    "scores": {
                        "pos": row["vader_pos"],
                        "neu": row["vader_neu"],
                        "neg": row["vader_neg"],
                        "compound": row["compound_score"],
                    },
                    "created_at": row["created_at"],
                }
            )

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "reviews": results,
        }
    finally:
        conn.close()


def get_history_stats() -> Dict[str, Any]:
    """Aggregate summary statistics for all saved reviews."""
    conn = get_db_connection()
    try:
        total = conn.execute("SELECT COUNT(*) FROM saved_reviews").fetchone()[0]
        text_count = conn.execute("SELECT COUNT(*) FROM saved_reviews WHERE source_type = 'text'").fetchone()[0]
        url_count = conn.execute("SELECT COUNT(*) FROM saved_reviews WHERE source_type = 'url'").fetchone()[0]

        pos_count = conn.execute("SELECT COUNT(*) FROM saved_reviews WHERE sentiment_label = 'Positive'").fetchone()[0]
        neu_count = conn.execute("SELECT COUNT(*) FROM saved_reviews WHERE sentiment_label = 'Neutral'").fetchone()[0]
        neg_count = conn.execute("SELECT COUNT(*) FROM saved_reviews WHERE sentiment_label = 'Negative'").fetchone()[0]

        avg_score_row = conn.execute("SELECT AVG(compound_score) FROM saved_reviews").fetchone()
        avg_score = round(float(avg_score_row[0]), 4) if avg_score_row and avg_score_row[0] is not None else 0.0

        return {
            "total_reviews": total,
            "text_count": text_count,
            "url_count": url_count,
            "positive_count": pos_count,
            "neutral_count": neu_count,
            "negative_count": neg_count,
            "average_compound_score": avg_score,
        }
    finally:
        conn.close()


def delete_saved_review(review_id: int) -> bool:
    """Delete a single review by ID."""
    conn = get_db_connection()
    try:
        with conn:
            cursor = conn.execute("DELETE FROM saved_reviews WHERE id = ?", (review_id,))
            return cursor.rowcount > 0
    finally:
        conn.close()


def clear_all_reviews() -> int:
    """Delete all saved reviews."""
    conn = get_db_connection()
    try:
        with conn:
            cursor = conn.execute("DELETE FROM saved_reviews")
            return cursor.rowcount
    finally:
        conn.close()
