"""
ReviewLens Unit Tests: Sentiment Analysis and Data Validators
============================================================
Comprehensive test suite covering VADER sentiment labeling, compound score thresholds,
edge cases, and dataset validation utilities.
"""

import pandas as pd
import pytest

from backend.sentiment import (
    analyze_review,
    analyze_reviews,
    compound_to_label,
    compound_to_strength,
)
from backend.validators import (
    RAW_SCHEMA_COLUMNS,
    is_valid_review_text,
    normalize_whitespace,
    safe_text,
    validate_dataset_schema,
    validate_non_negative_integer,
    validate_rating,
    validate_required_columns,
)


class TestSentimentAnalysis:
    """Test suite for VADER sentiment analysis engine and threshold labeling."""

    def test_clearly_positive_review(self):
        """Test a strongly positive customer review."""
        review_text = "Excellent quality, fast delivery, and I absolutely love it."
        result = analyze_review(review_text)

        assert result["sentiment_label"] == "Positive"
        assert result["compound_score"] > 0.05
        assert result["vader_pos"] > 0.0
        assert result["sentiment_strength"] in {"Positive", "Strong Positive"}

    def test_clearly_negative_review(self):
        """Test a strongly negative customer review."""
        review_text = "Terrible product. It stopped working after one day and support was unhelpful."
        result = analyze_review(review_text)

        assert result["sentiment_label"] == "Negative"
        assert result["compound_score"] < -0.05
        assert result["vader_neg"] > 0.0
        assert result["sentiment_strength"] in {"Negative", "Strong Negative"}

    def test_neutral_review_and_vader_lexicon_behavior(self):
        """
        Test the review: 'The product arrived as described. It is okay for the price.'
        
        NOTE on VADER Lexicon Behavior:
        Human annotators may consider this neutral/mildly lukewarm. However, in VADER's
        rule-based lexicon, the token 'okay' carries a positive valence (+0.9), which
        produces a compound score of ~0.2263. Because 0.2263 >= 0.05, VADER classifies
        it as 'Positive'. This test documents this exact threshold and lexicon result.
        We also verify an unambiguously neutral statement with zero valence tokens.
        """
        review_text = "The product arrived as described. It is okay for the price."
        result = analyze_review(review_text)
        
        # Document actual VADER behavior
        assert result["compound_score"] == 0.2263
        assert result["sentiment_label"] == "Positive"

        # Strictly neutral sentence with no emotive tokens produces Neutral
        strictly_neutral = "The product arrived in a cardboard box on Tuesday."
        neutral_result = analyze_review(strictly_neutral)
        assert neutral_result["compound_score"] == 0.0
        assert neutral_result["sentiment_label"] == "Neutral"
        assert neutral_result["sentiment_strength"] == "Neutral"

    def test_threshold_behavior(self):
        """
        Verify exact boundary condition behavior for compound_to_label:
        - compound >= 0.05  -> Positive
        - compound <= -0.05 -> Negative
        - -0.05 < compound < 0.05 -> Neutral
        """
        assert compound_to_label(0.05) == "Positive"
        assert compound_to_label(0.50) == "Positive"
        assert compound_to_label(1.0) == "Positive"

        assert compound_to_label(-0.05) == "Negative"
        assert compound_to_label(-0.50) == "Negative"
        assert compound_to_label(-1.0) == "Negative"

        assert compound_to_label(0.0) == "Neutral"
        assert compound_to_label(0.049) == "Neutral"
        assert compound_to_label(-0.049) == "Neutral"

    def test_strength_tiers(self):
        """Verify 5-tier sentiment strength classification."""
        assert compound_to_strength(0.85) == "Strong Positive"
        assert compound_to_strength(0.60) == "Strong Positive"
        assert compound_to_strength(0.35) == "Positive"
        assert compound_to_strength(0.05) == "Positive"
        assert compound_to_strength(0.0) == "Neutral"
        assert compound_to_strength(-0.04) == "Neutral"
        assert compound_to_strength(-0.25) == "Negative"
        assert compound_to_strength(-0.60) == "Strong Negative"
        assert compound_to_strength(-0.85) == "Strong Negative"

    def test_batch_analyze_reviews(self):
        """Verify batch review analysis."""
        texts = [
            "Outstanding device, highly recommend!",
            "Completely broke within 2 hours, do not buy.",
            "Items were delivered inside a parcel.",
        ]
        results = analyze_reviews(texts)
        assert len(results) == 3
        assert results[0]["sentiment_label"] == "Positive"
        assert results[1]["sentiment_label"] == "Negative"
        assert results[2]["sentiment_label"] == "Neutral"


class TestValidators:
    """Test suite for data validation and sanitization functions."""

    def test_validate_rating(self):
        """Check rating integer validation for 1 to 5."""
        assert validate_rating(1) == 1
        assert validate_rating(3) == 3
        assert validate_rating(5) == 5
        assert validate_rating("4") == 4
        assert validate_rating(4.0) == 4

        # Invalid ratings
        assert validate_rating(0) is None
        assert validate_rating(6) is None
        assert validate_rating(-1) is None
        assert validate_rating(3.5) is None
        assert validate_rating("not_a_rating") is None
        assert validate_rating(None) is None

    def test_validate_non_negative_integer(self):
        """Check non-negative integer validation for votes/counts."""
        assert validate_non_negative_integer(0) == 0
        assert validate_non_negative_integer(15) == 15
        assert validate_non_negative_integer("42") == 42
        assert validate_non_negative_integer(-5) is None
        assert validate_non_negative_integer(3.14) is None
        assert validate_non_negative_integer(None) is None

    def test_normalize_whitespace(self):
        """Check whitespace collapsing and stripping."""
        raw = "   This   is   a   \n\t  test review.   "
        assert normalize_whitespace(raw) == "This is a test review."
        assert normalize_whitespace("") == ""
        assert normalize_whitespace(None) == ""

    def test_safe_text(self):
        """Check null/none-safe string conversion."""
        assert safe_text("  hello  ") == "hello"
        assert safe_text(None) == ""
        assert safe_text(float("nan")) == ""
        assert safe_text(123) == "123"

    def test_is_valid_review_text(self):
        """Check review text validity logic."""
        assert is_valid_review_text("Great product!") is True
        assert is_valid_review_text("ok") is True
        assert is_valid_review_text("") is False
        assert is_valid_review_text("     ") is False
        assert is_valid_review_text(None) is False
        assert is_valid_review_text("!!!") is False

    def test_validate_required_columns(self):
        """Check column presence validation."""
        df = pd.DataFrame(columns=["a", "b", "c"])
        assert validate_required_columns(df, ["a", "b"]) is True

        with pytest.raises(ValueError, match="missing required columns"):
            validate_required_columns(df, ["a", "z"])

    def test_validate_dataset_schema(self):
        """Check complete dataset schema validation."""
        valid_df = pd.DataFrame(columns=RAW_SCHEMA_COLUMNS)
        result = validate_dataset_schema(valid_df)
        assert result["is_valid"] is True
        assert len(result["missing_columns"]) == 0

        invalid_df = pd.DataFrame(columns=["review_id", "product_name"])
        invalid_result = validate_dataset_schema(invalid_df)
        assert invalid_result["is_valid"] is False
        assert len(invalid_result["missing_columns"]) > 0


class TestPipeline:
    """Test suite for pipeline data generation, cleaning, and table exports."""

    def test_synthetic_data_generation(self):
        """Verify synthetic dataset generator conforms to requirements."""
        from backend.data_generator import generate_synthetic_reviews

        df = generate_synthetic_reviews(target_count=210, seed=42)
        assert len(df) >= 150
        assert len(df) <= 300
        assert all(col in df.columns for col in RAW_SCHEMA_COLUMNS)
        assert df["data_mode"].iloc[0] == "DEMO"
        assert df["source"].iloc[0] == "Demo Dataset"
        assert df["product_category"].nunique() >= 5
        assert df["product_name"].nunique() >= 10

    def test_data_cleaning_pipeline(self):
        """Verify that cleaning removes invalid ratings, invalid texts, and duplicates."""
        from backend.data_generator import generate_synthetic_reviews
        from backend.pipeline import clean_review_dataset, apply_vader_sentiment, generate_summary_tables

        df_raw = generate_synthetic_reviews(target_count=210, seed=42)
        df_cleaned, summary, invalid_ratings = clean_review_dataset(df_raw)

        # Ensure invalid ratings were removed
        assert len(invalid_ratings) > 0
        assert all(r in {1, 2, 3, 4, 5} for r in df_cleaned["rating"])
        
        # Ensure duplicates and empty texts were removed
        assert not df_cleaned.duplicated(subset=["cleaned_review_text"]).any()
        assert df_cleaned["cleaned_review_text"].apply(lambda t: len(t.strip()) > 0).all()

        # Check sentiment enrichment
        df_sentiment = apply_vader_sentiment(df_cleaned)
        assert "compound_score" in df_sentiment.columns
        assert "sentiment_label" in df_sentiment.columns
        assert "sentiment_strength" in df_sentiment.columns
        assert "rating_sentiment_match" in df_sentiment.columns

        # Check summary tables
        tables = generate_summary_tables(df_sentiment)
        assert "sentiment_summary" in tables
        assert "product_sentiment_summary" in tables
        assert "category_sentiment_summary" in tables
        assert "top_positive_reviews" in tables
        assert "top_negative_reviews" in tables
        assert len(tables["top_positive_reviews"]) == 10
        assert len(tables["top_negative_reviews"]) == 10

