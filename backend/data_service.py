"""
ReviewLens Data Service Layer
=============================
Provides clean, cached, thread-safe access to processed review datasets,
aggregations, pagination, filtering, and summary metrics.
Ensures no internal filesystem paths or unhandled NaNs are exposed to API consumers.
"""

from __future__ import annotations

import math
from pathlib import Path
import threading
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from backend.config import get_settings
from backend.exceptions import DatasetNotFoundError, DatasetValidationError
from backend.logging_config import get_logger

logger = get_logger("data_service")

# Thread-safe caching
_CACHE_LOCK = threading.Lock()
_CACHED_DF: Optional[pd.DataFrame] = None

# Relative path constant for public display
PUBLIC_DATASET_REL_PATH = "data/processed/reviews_with_sentiment.csv"

# Required columns in the enriched dataset
REQUIRED_ENRICHED_COLUMNS = [
    "review_id",
    "product_name",
    "product_category",
    "source",
    "review_title",
    "review_text",
    "rating",
    "compound_score",
    "sentiment_label",
    "sentiment_strength",
    "vader_neg",
    "vader_neu",
    "vader_pos",
]


def get_project_root() -> Path:
    """
    Resolve the absolute root directory of the ReviewLens project.

    Returns:
        Path object pointing to repository root.
    """
    # Assuming this file is at backend/data_service.py -> root is parent of backend
    return Path(__file__).resolve().parent.parent


def get_enriched_dataset_path() -> Path:
    """
    Get the absolute file path to the enriched processed dataset CSV.

    Returns:
        Path to data/processed/reviews_with_sentiment.csv
    """
    return get_project_root() / "data" / "processed" / "reviews_with_sentiment.csv"


def clean_record_for_json(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean NaN, null, and numpy scalar types from a dictionary for JSON compliance.

    Args:
        record: Dictionary representing a DataFrame row.

    Returns:
        Sanitized dictionary with native Python types and None for NaNs.
    """
    cleaned: Dict[str, Any] = {}
    for key, value in record.items():
        if value is None or pd.isna(value):
            if key == "review_title":
                cleaned[key] = ""
            else:
                cleaned[key] = None
        elif isinstance(value, (np.floating, float)):

            if math.isnan(value) or math.isinf(value):
                cleaned[key] = None
            else:
                cleaned[key] = float(value)
        elif isinstance(value, (np.integer, int)):
            cleaned[key] = int(value)
        elif isinstance(value, (np.bool_, bool)):
            cleaned[key] = bool(value)
        elif isinstance(value, pd.Timestamp):
            cleaned[key] = value.strftime("%Y-%m-%d")
        else:
            cleaned[key] = str(value)
    return cleaned


def load_enriched_reviews(force_reload: bool = False) -> pd.DataFrame:
    """
    Load the enriched review dataset into an in-memory cached DataFrame.
    Guarantees thread safety and returns a defensive copy.

    Args:
        force_reload: If True, bypasses cache and reads fresh from CSV.

    Returns:
        Defensive copy of the enriched pandas DataFrame.

    Raises:
        DatasetNotFoundError: If the CSV file does not exist.
        DatasetValidationError: If dataset is empty or missing required schema columns.
    """
    global _CACHED_DF

    with _CACHE_LOCK:
        if _CACHED_DF is not None and not force_reload:
            return _CACHED_DF.copy()

        csv_path = get_enriched_dataset_path()
        if not csv_path.exists():
            logger.error("Dataset not found at expected path: %s", csv_path)
            raise DatasetNotFoundError(
                f"Enriched review dataset was not found at '{PUBLIC_DATASET_REL_PATH}'. "
                "Ensure that Phase 1 & 2 pipelines have been executed to generate this file."
            )

        try:
            df = pd.read_csv(csv_path)
        except Exception as exc:
            logger.error("Failed to read dataset file: %s", exc)
            raise DatasetValidationError(f"Could not read dataset CSV: {exc}") from exc

        if df.empty:
            raise DatasetValidationError("Enriched review dataset is empty.")

        missing_cols = [col for col in REQUIRED_ENRICHED_COLUMNS if col not in df.columns]
        if missing_cols:
            raise DatasetValidationError(
                f"Enriched review dataset is missing mandatory columns: {missing_cols}"
            )

        # Ensure review_date is properly formatted string or timestamp
        if "review_date" in df.columns:
            df["review_date_parsed"] = pd.to_datetime(df["review_date"], errors="coerce")
            # Default sort newest first
            df = df.sort_values(by="review_date_parsed", ascending=False, na_position="last").reset_index(drop=True)
            df.drop(columns=["review_date_parsed"], inplace=True, errors="ignore")

        _CACHED_DF = df
        logger.info("Loaded %d enriched reviews into memory cache.", len(_CACHED_DF))
        return _CACHED_DF.copy()


def get_dataset_metadata() -> Dict[str, Any]:
    """
    Retrieve high-level metadata regarding the local dataset and backend capabilities.

    Returns:
        Dictionary detailing dataset mode, record counts, and feature flags.
    """
    df = load_enriched_reviews()
    settings = get_settings()

    data_mode = str(df["data_mode"].iloc[0]) if "data_mode" in df.columns and not df.empty else "DEMO"
    source_counts = df["source"].value_counts().to_dict() if "source" in df.columns else {}

    return {
        "status": "success",
        "data_mode": data_mode,
        "dataset_path": PUBLIC_DATASET_REL_PATH,
        "total_reviews": int(len(df)),
        "source_counts": {str(k): int(v) for k, v in source_counts.items()},
        "supported_features": [
            "VADER Sentiment Analysis",
            "5-Tier Sentiment Intensity",
            "Interactive Demo Data Browsing",
            "Product & Category Aggregations",
            "SSRF-Protected URL Validation",
            "Controlled Playwright Scraping Architecture",
        ],
        "scraping_enabled": bool(settings.ENABLE_PLAYWRIGHT_SCRAPING),
    }


def get_sentiment_summary() -> Dict[str, Any]:
    """
    Retrieve overall sentiment summary statistics, using precomputed output table
    if available, or dynamically computing metrics across the dataset.

    Returns:
        Dictionary matching SentimentSummaryResponse schema.
    """
    root = get_project_root()
    summary_path = root / "output" / "tables" / "sentiment_summary.csv"

    if summary_path.exists():
        try:
            summary_df = pd.read_csv(summary_path)
            if not summary_df.empty:
                row = summary_df.iloc[0].to_dict()
                return {
                    "status": "success",
                    "total_reviews": int(row.get("total_reviews", 0)),
                    "positive_count": int(row.get("positive_count", 0)),
                    "neutral_count": int(row.get("neutral_count", 0)),
                    "negative_count": int(row.get("negative_count", 0)),
                    "positive_percentage": round(float(row.get("positive_percentage", 0.0)), 2),
                    "neutral_percentage": round(float(row.get("neutral_percentage", 0.0)), 2),
                    "negative_percentage": round(float(row.get("negative_percentage", 0.0)), 2),
                    "average_compound_score": round(float(row.get("average_compound_score", 0.0)), 4),
                    "median_compound_score": round(float(row.get("median_compound_score", 0.0)), 4),
                    "average_rating": round(float(row.get("average_rating", 0.0)), 2),
                    "sentiment_match_percentage": (
                        round(float(row.get("sentiment_match_percentage")), 2)
                        if pd.notna(row.get("sentiment_match_percentage"))
                        else None
                    ),
                }
        except Exception as exc:
            logger.warning("Could not read precomputed sentiment summary, calculating dynamically: %s", exc)

    # Dynamic fallback calculation
    df = load_enriched_reviews()
    total = len(df)
    pos_count = int((df["sentiment_label"] == "Positive").sum())
    neu_count = int((df["sentiment_label"] == "Neutral").sum())
    neg_count = int((df["sentiment_label"] == "Negative").sum())

    pos_pct = round((pos_count / total) * 100, 2) if total > 0 else 0.0
    neu_pct = round((neu_count / total) * 100, 2) if total > 0 else 0.0
    neg_pct = round((neg_count / total) * 100, 2) if total > 0 else 0.0

    avg_compound = round(float(df["compound_score"].mean()), 4) if total > 0 else 0.0
    median_compound = round(float(df["compound_score"].median()), 4) if total > 0 else 0.0
    avg_rating = round(float(df["rating"].mean()), 2) if "rating" in df.columns and total > 0 else 0.0

    match_pct = None
    if "rating_sentiment_match" in df.columns and total > 0:
        match_series = df["rating_sentiment_match"].dropna()
        if not match_series.empty:
            match_pct = round(float(match_series.mean() * 100), 2)

    return {
        "status": "success",
        "total_reviews": total,
        "positive_count": pos_count,
        "neutral_count": neu_count,
        "negative_count": neg_count,
        "positive_percentage": pos_pct,
        "neutral_percentage": neu_pct,
        "negative_percentage": neg_pct,
        "average_compound_score": avg_compound,
        "median_compound_score": median_compound,
        "average_rating": avg_rating,
        "sentiment_match_percentage": match_pct,
    }


def get_reviews_paginated(
    limit: int = 20,
    offset: int = 0,
    sentiment: Optional[str] = None,
    category: Optional[str] = None,
    product: Optional[str] = None,
) -> Tuple[int, pd.DataFrame]:
    """
    Retrieve paginated reviews filtered by sentiment, category, and product.

    Args:
        limit: Number of records to return.
        offset: Record offset for pagination.
        sentiment: Optional sentiment label filter (Positive, Neutral, Negative).
        category: Optional product category filter.
        product: Optional product name filter (case-insensitive substring).

    Returns:
        Tuple of (total_filtered_count, paginated_dataframe).
    """
    df = load_enriched_reviews()

    if sentiment:
        df = df[df["sentiment_label"].astype(str).str.lower() == sentiment.strip().lower()]

    if category:
        df = df[df["product_category"].astype(str).str.lower() == category.strip().lower()]

    if product:
        df = df[df["product_name"].astype(str).str.lower().str.contains(product.strip().lower(), regex=False)]

    total_count = len(df)
    paginated_df = df.iloc[offset : offset + limit]

    return total_count, paginated_df


def get_product_summaries() -> List[Dict[str, Any]]:
    """
    Retrieve product-level sentiment and rating summaries.
    Sorted by review_count descending, then average_compound_score descending.

    Returns:
        List of dictionaries conforming to ProductSummaryResponse.
    """
    root = get_project_root()
    product_summary_path = root / "output" / "tables" / "product_sentiment_summary.csv"

    if product_summary_path.exists():
        try:
            prod_df = pd.read_csv(product_summary_path)
            if not prod_df.empty:
                prod_df = prod_df.sort_values(
                    by=["review_count", "average_compound_score"],
                    ascending=[False, False],
                )
                records = [clean_record_for_json(row) for row in prod_df.to_dict(orient="records")]
                return records
        except Exception as exc:
            logger.warning("Failed reading product_sentiment_summary.csv, computing dynamically: %s", exc)

    # Dynamic calculation
    df = load_enriched_reviews()
    records: List[Dict[str, Any]] = []

    for (prod_name, prod_cat), group in df.groupby(["product_name", "product_category"]):
        count = len(group)
        pos_cnt = (group["sentiment_label"] == "Positive").sum()
        neg_cnt = (group["sentiment_label"] == "Negative").sum()
        avg_rat = float(group["rating"].mean()) if "rating" in group.columns else 0.0
        avg_comp = float(group["compound_score"].mean()) if "compound_score" in group.columns else 0.0
        avg_wc = float(group["word_count"].mean()) if "word_count" in group.columns else 0.0

        records.append({
            "product_name": str(prod_name),
            "product_category": str(prod_cat),
            "review_count": int(count),
            "average_rating": round(avg_rat, 2),
            "average_compound_score": round(avg_comp, 4),
            "positive_percentage": round((pos_cnt / count) * 100, 2) if count > 0 else 0.0,
            "negative_percentage": round((neg_cnt / count) * 100, 2) if count > 0 else 0.0,
            "average_word_count": round(avg_wc, 1),
        })

    records.sort(key=lambda r: (r["review_count"], r["average_compound_score"]), reverse=True)
    return records


def get_category_summaries() -> List[Dict[str, Any]]:
    """
    Retrieve category-level sentiment and rating summaries.
    Sorted by review_count descending.

    Returns:
        List of dictionaries conforming to CategorySummaryResponse.
    """
    root = get_project_root()
    cat_summary_path = root / "output" / "tables" / "category_sentiment_summary.csv"

    if cat_summary_path.exists():
        try:
            cat_df = pd.read_csv(cat_summary_path)
            if not cat_df.empty:
                cat_df = cat_df.sort_values(by="review_count", ascending=False)
                records = [clean_record_for_json(row) for row in cat_df.to_dict(orient="records")]
                return records
        except Exception as exc:
            logger.warning("Failed reading category_sentiment_summary.csv, computing dynamically: %s", exc)

    # Dynamic calculation
    df = load_enriched_reviews()
    records: List[Dict[str, Any]] = []

    for cat_name, group in df.groupby("product_category"):
        count = len(group)
        pos_cnt = (group["sentiment_label"] == "Positive").sum()
        neg_cnt = (group["sentiment_label"] == "Negative").sum()
        avg_rat = float(group["rating"].mean()) if "rating" in group.columns else 0.0
        avg_comp = float(group["compound_score"].mean()) if "compound_score" in group.columns else 0.0

        records.append({
            "product_category": str(cat_name),
            "review_count": int(count),
            "average_rating": round(avg_rat, 2),
            "average_compound_score": round(avg_comp, 4),
            "positive_percentage": round((pos_cnt / count) * 100, 2) if count > 0 else 0.0,
            "negative_percentage": round((neg_cnt / count) * 100, 2) if count > 0 else 0.0,
        })

    records.sort(key=lambda r: r["review_count"], reverse=True)
    return records


def get_top_reviews(sentiment: str, limit: int = 10) -> pd.DataFrame:
    """
    Retrieve top reviews ordered by compound score for a given sentiment category.
    Positive returns highest compound scores; Negative returns lowest compound scores.

    Args:
        sentiment: Sentiment label ("Positive" or "Negative", case-insensitive).
        limit: Number of records to return.

    Returns:
        DataFrame containing top matching review records.

    Raises:
        ValueError: If sentiment is not Positive or Negative.
    """
    norm_sentiment = sentiment.strip().title()
    if norm_sentiment not in {"Positive", "Negative"}:
        raise ValueError(
            f"Invalid sentiment filter '{sentiment}'. Top reviews must be requested for 'Positive' or 'Negative'."
        )

    df = load_enriched_reviews()
    subset = df[df["sentiment_label"] == norm_sentiment].copy()

    if norm_sentiment == "Positive":
        # Highest compound score first
        subset = subset.sort_values(
            by=["compound_score", "helpful_votes"],
            ascending=[False, False],
        )
    else:
        # Lowest (most negative) compound score first
        subset = subset.sort_values(
            by=["compound_score", "helpful_votes"],
            ascending=[True, False],
        )

    return subset.head(limit)
