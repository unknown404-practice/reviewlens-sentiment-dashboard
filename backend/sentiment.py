"""
ReviewLens Sentiment Analysis Module
====================================
VADER-based sentiment analysis engine providing compound score calculation,
categorical sentiment labelling, and intensity segmentation for product reviews.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from backend.validators import safe_text

# Initialize singleton analyzer instance
_analyzer: SentimentIntensityAnalyzer | None = None


def get_analyzer() -> SentimentIntensityAnalyzer:
    """
    Get or lazily initialize the VADER SentimentIntensityAnalyzer instance.

    Returns:
        SentimentIntensityAnalyzer instance.
    """
    global _analyzer
    if _analyzer is None:
        _analyzer = SentimentIntensityAnalyzer()
    return _analyzer


def compound_to_label(compound: float) -> str:
    """
    Convert a VADER compound score to a 3-class sentiment label using standard thresholds.

    Thresholds:
        - compound >= 0.05  -> Positive
        - compound <= -0.05 -> Negative
        - otherwise         -> Neutral

    Args:
        compound: VADER compound score in [-1.0, 1.0].

    Returns:
        'Positive', 'Negative', or 'Neutral'.
    """
    if compound >= 0.05:
        return "Positive"
    elif compound <= -0.05:
        return "Negative"
    else:
        return "Neutral"


def compound_to_strength(compound: float) -> str:
    """
    Segment compound score into 5 granular sentiment strength tiers.

    Tiers:
        - compound >= 0.60                  -> Strong Positive
        - 0.05 <= compound < 0.60           -> Positive
        - -0.05 < compound < 0.05           -> Neutral
        - -0.60 < compound <= -0.05         -> Negative
        - compound <= -0.60                 -> Strong Negative

    Args:
        compound: VADER compound score in [-1.0, 1.0].

    Returns:
        Sentiment strength string.
    """
    if compound >= 0.60:
        return "Strong Positive"
    elif compound >= 0.05:
        return "Positive"
    elif compound > -0.05:
        return "Neutral"
    elif compound > -0.60:
        return "Negative"
    else:
        return "Strong Negative"


def analyze_review(text: str) -> Dict[str, Any]:
    """
    Analyze the sentiment of a single review text string using VADER.

    Args:
        text: Input review text.

    Returns:
        Dictionary containing:
            - vader_neg: float (rounded to 4 decimals)
            - vader_neu: float (rounded to 4 decimals)
            - vader_pos: float (rounded to 4 decimals)
            - compound_score: float (rounded to 4 decimals)
            - sentiment_label: str ('Positive', 'Neutral', 'Negative')
            - sentiment_strength: str (5-tier intensity)
            - score_abs: float (absolute compound score)
    """
    analyzer = get_analyzer()
    sanitized = safe_text(text)
    if not sanitized:
        scores = {"neg": 0.0, "neu": 1.0, "pos": 0.0, "compound": 0.0}
    else:
        scores = analyzer.polarity_scores(sanitized)

    compound = round(float(scores["compound"]), 4)
    vader_neg = round(float(scores["neg"]), 4)
    vader_neu = round(float(scores["neu"]), 4)
    vader_pos = round(float(scores["pos"]), 4)
    label = compound_to_label(compound)
    strength = compound_to_strength(compound)
    score_abs = round(abs(compound), 4)

    return {
        "vader_neg": vader_neg,
        "vader_neu": vader_neu,
        "vader_pos": vader_pos,
        "compound_score": compound,
        "sentiment_label": label,
        "sentiment_strength": strength,
        "score_abs": score_abs,
    }


def analyze_reviews(texts: List[str]) -> List[Dict[str, Any]]:
    """
    Batch sentiment analysis across a list of review text strings.

    Args:
        texts: List of review text strings.

    Returns:
        List of sentiment analysis result dictionaries.
    """
    return [analyze_review(t) for t in texts]
