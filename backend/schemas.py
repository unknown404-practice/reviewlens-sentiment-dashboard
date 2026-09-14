"""
ReviewLens Pydantic Schemas Module
==================================
Strict, typed request and response schemas with comprehensive documentation,
constraints, and validations across all API endpoints.
"""

from __future__ import annotations

from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator

from backend.validators import validate_public_http_url


# ==============================================================================
# 1. System Schemas
# ==============================================================================

class RootResponse(BaseModel):
    """Welcome and index response model."""
    status: str = Field(default="success", description="Response status indicator")
    message: str = Field(..., description="Informational greeting")
    docs_url: str = Field(default="/docs", description="Interactive OpenAPI documentation URL")
    health_url: str = Field(default="/health", description="Health check endpoint URL")
    api_version: str = Field(default="v1", description="Current API route version")


class HealthResponse(BaseModel):
    """Service health and environment status."""
    status: str = Field(default="healthy", description="Operational health status")
    service: str = Field(..., description="Service identifier name")
    version: str = Field(..., description="Service semantic version")
    environment: str = Field(..., description="Active runtime environment")


class ApiErrorResponse(BaseModel):
    """Standardized error envelope for client and server errors."""
    status: str = Field(default="error", description="Error status indicator")
    message: str = Field(..., description="Human-readable error description")
    detail: Optional[str] = Field(default=None, description="Safe contextual error detail")


class SourceInfoResponse(BaseModel):
    """Dataset provenance and active capability information."""
    status: str = Field(default="success", description="Response status indicator")
    data_mode: str = Field(..., description="Dataset operation mode, e.g. DEMO or LIVE")
    dataset_path: str = Field(..., description="Relative project path to the active review dataset")
    total_reviews: int = Field(..., ge=0, description="Total number of reviews available in the active dataset")
    source_counts: Dict[str, int] = Field(..., description="Review count breakdown by original source")
    supported_features: List[str] = Field(..., description="List of platform capability descriptors")
    scraping_enabled: bool = Field(..., description="Whether live Playwright scraping is enabled in configuration")


# ==============================================================================
# 2. Sentiment Analysis Schemas
# ==============================================================================

class SentimentScores(BaseModel):
    """VADER sentiment score components."""
    neg: float = Field(..., description="Negative sentiment proportion [0.0, 1.0]")
    neu: float = Field(..., description="Neutral sentiment proportion [0.0, 1.0]")
    pos: float = Field(..., description="Positive sentiment proportion [0.0, 1.0]")
    compound: float = Field(..., description="Compound normalized sentiment score [-1.0, 1.0]")


class TextAnalysisRequest(BaseModel):
    """Request payload for text-level sentiment analysis."""
    text: str = Field(
        ...,
        description="Review text string to analyze (1 to 5000 characters).",
        examples=["Excellent quality, fast delivery, and I absolutely love it."],
    )

    @field_validator("text", mode="before")
    @classmethod
    def validate_text(cls, v: object) -> str:
        """Ensure input text is non-empty, non-whitespace, and within size constraints."""
        if not isinstance(v, str):
            raise ValueError("Review text must be a valid string.")
        stripped = v.strip()
        if not stripped:
            raise ValueError("Review text cannot be empty or whitespace-only.")
        if len(stripped) > 5000:
            raise ValueError("Review text exceeds maximum allowed length of 5000 characters.")
        return stripped


class TextAnalysisResponse(BaseModel):
    """Response payload for text-level sentiment analysis."""
    status: str = Field(default="success", description="Analysis status indicator")
    text: str = Field(..., description="The analyzed review text")
    sentiment_label: str = Field(..., description="Categorical sentiment label: Positive, Neutral, or Negative")
    sentiment_strength: str = Field(..., description="Granular 5-tier intensity: Strong Positive, Positive, Neutral, Negative, Strong Negative")
    scores: SentimentScores = Field(..., description="Detailed VADER component scores")
    saved_id: Optional[int] = Field(default=None, description="SQLite record ID if persisted")
    rating: Optional[float] = Field(default=None, description="Optional star rating")
    author: Optional[str] = Field(default=None, description="Review author or reviewer name")


# ==============================================================================
# 3. Demo Data & Review Schemas
# ==============================================================================

class ReviewResponse(BaseModel):
    """Detailed representation of an individual enriched product review."""
    review_id: str = Field(..., description="Unique review record identifier")
    product_name: str = Field(..., description="Commercial product name")
    product_category: str = Field(..., description="Product category hierarchy")
    source: str = Field(..., description="Review origin or marketplace identifier")
    review_title: Optional[str] = Field(default="", description="Short headline or review title")
    review_text: str = Field(..., description="Complete body text of the customer review")
    rating: float = Field(..., ge=1.0, le=5.0, description="Customer rating on a 1-5 scale")
    review_date: Optional[str] = Field(default=None, description="Publication date of the review (YYYY-MM-DD)")
    verified_purchase: bool = Field(..., description="Whether the reviewer made a verified purchase")
    helpful_votes: int = Field(..., ge=0, description="Count of helpful feedback votes received")
    sentiment_label: str = Field(..., description="Categorical sentiment: Positive, Neutral, or Negative")
    sentiment_strength: str = Field(..., description="5-tier sentiment intensity classification")
    compound_score: float = Field(..., description="VADER compound score in [-1.0, 1.0]")
    vader_neg: float = Field(..., description="VADER negative proportion")
    vader_neu: float = Field(..., description="VADER neutral proportion")
    vader_pos: float = Field(..., description="VADER positive proportion")
    word_count: Optional[int] = Field(default=None, ge=0, description="Word count of the cleaned review text")
    rating_group: Optional[str] = Field(default=None, description="Rating tier: Positive (4-5), Neutral (3), Negative (1-2)")
    rating_sentiment_match: Optional[bool] = Field(default=None, description="Whether rating aligns with VADER classification")

    @field_validator("review_title", mode="before")
    @classmethod
    def sanitize_title(cls, v: object) -> str:
        """Handle null or missing review titles safely."""
        if v is None:
            return ""
        return str(v).strip()



class PaginatedReviewsResponse(BaseModel):
    """Paginated collection of enriched product reviews."""
    status: str = Field(default="success", description="Response status indicator")
    total: int = Field(..., ge=0, description="Total number of reviews matching the filter criteria")
    limit: int = Field(..., ge=1, description="Page limit applied to the query")
    offset: int = Field(..., ge=0, description="Page offset applied to the query")
    reviews: List[ReviewResponse] = Field(..., description="List of review items for the current page")


# ==============================================================================
# 4. Analytics Schemas
# ==============================================================================

class SentimentSummaryResponse(BaseModel):
    """Dataset-wide sentiment aggregation metrics."""
    status: str = Field(default="success", description="Response status indicator")
    total_reviews: int = Field(..., ge=0, description="Total number of analyzed reviews")
    positive_count: int = Field(..., ge=0, description="Count of positive reviews")
    neutral_count: int = Field(..., ge=0, description="Count of neutral reviews")
    negative_count: int = Field(..., ge=0, description="Count of negative reviews")
    positive_percentage: float = Field(..., ge=0.0, le=100.0, description="Percentage of reviews classified as Positive")
    neutral_percentage: float = Field(..., ge=0.0, le=100.0, description="Percentage of reviews classified as Neutral")
    negative_percentage: float = Field(..., ge=0.0, le=100.0, description="Percentage of reviews classified as Negative")
    average_compound_score: float = Field(..., ge=-1.0, le=1.0, description="Mean VADER compound score across all reviews")
    median_compound_score: float = Field(..., ge=-1.0, le=1.0, description="Median VADER compound score across all reviews")
    average_rating: float = Field(..., ge=0.0, le=5.0, description="Mean customer star rating")
    sentiment_match_percentage: Optional[float] = Field(default=None, ge=0.0, le=100.0, description="Percentage where rating aligns with sentiment")


class ProductSummaryResponse(BaseModel):
    """Aggregated sentiment and rating metrics for a specific product."""
    product_name: str = Field(..., description="Commercial product name")
    product_category: str = Field(..., description="Product category hierarchy")
    review_count: int = Field(..., ge=0, description="Total reviews for this product")
    average_rating: float = Field(..., ge=0.0, le=5.0, description="Mean star rating")
    average_compound_score: float = Field(..., ge=-1.0, le=1.0, description="Mean VADER compound score")
    positive_percentage: float = Field(..., ge=0.0, le=100.0, description="Positive review percentage")
    negative_percentage: float = Field(..., ge=0.0, le=100.0, description="Negative review percentage")
    average_word_count: float = Field(..., ge=0.0, description="Mean review word count")


class CategorySummaryResponse(BaseModel):
    """Aggregated sentiment and rating metrics for a product category."""
    product_category: str = Field(..., description="Product category name")
    review_count: int = Field(..., ge=0, description="Total reviews in this category")
    average_rating: float = Field(..., ge=0.0, le=5.0, description="Mean star rating")
    average_compound_score: float = Field(..., ge=-1.0, le=1.0, description="Mean VADER compound score")
    positive_percentage: float = Field(..., ge=0.0, le=100.0, description="Positive review percentage")
    negative_percentage: float = Field(..., ge=0.0, le=100.0, description="Negative review percentage")


# ==============================================================================
# 5. Scraping Schemas
# ==============================================================================

class ScrapeAnalyzeRequest(BaseModel):
    """Request payload to extract and analyze reviews from a permitted public URL."""
    url: str = Field(..., description="Permitted public webpage URL containing reviews")
    max_reviews: int = Field(default=20, ge=1, le=50, description="Maximum number of reviews to extract (1-50)")
    preview: Optional[bool] = Field(default=True, description="Enable resilient live preview extraction")

    @field_validator("url", mode="before")
    @classmethod
    def validate_target_url(cls, v: object) -> str:
        """Validate that input URL is non-empty, valid HTTP/HTTPS, and not a private host."""
        if not isinstance(v, str) or not v.strip():
            raise ValueError("URL cannot be empty or whitespace-only.")
        return validate_public_http_url(v.strip())


class ScrapeAnalysisResponse(BaseModel):
    """Response containing extracted and sentiment-analyzed reviews from a live URL."""
    status: str = Field(default="success", description="Extraction status indicator")
    message: str = Field(..., description="Extraction result summary")
    source_url: str = Field(..., description="The verified public source URL that was analyzed")
    page_title: Optional[str] = Field(default=None, description="Extracted webpage or product title")
    meta_description: Optional[str] = Field(default=None, description="Extracted meta description or summary")
    hostname: Optional[str] = Field(default=None, description="Domain hostname of the source")
    total: int = Field(..., ge=0, description="Number of reviews successfully extracted and scored")
    saved_to_db: Optional[bool] = Field(default=True, description="Indicates whether reviews were saved into SQLite")
    average_compound_score: Optional[float] = Field(default=None, description="Mean compound score for the page")
    positive_percentage: Optional[float] = Field(default=None, description="Percentage of positive opinions")
    neutral_percentage: Optional[float] = Field(default=None, description="Percentage of neutral opinions")
    negative_percentage: Optional[float] = Field(default=None, description="Percentage of negative opinions")
    reviews: List[TextAnalysisResponse] = Field(..., description="Scored review items")


# ==============================================================================
# 6. SQLite Saved Review & History Schemas
# ==============================================================================

class SavedReviewResponse(BaseModel):
    """Schema representing an individual review stored in the SQLite database."""
    id: int = Field(..., description="Unique database row ID")
    source_type: str = Field(..., description="'text' or 'url'")
    source_url: Optional[str] = Field(default=None, description="Source URL for URL extractions")
    page_title: Optional[str] = Field(default=None, description="Webpage or product title")
    product_name: Optional[str] = Field(default="Custom Analysis", description="Product identifier")
    product_category: Optional[str] = Field(default="General", description="Category classification")
    review_text: str = Field(..., description="Review content body")
    rating: Optional[float] = Field(default=None, description="Associated star rating")
    sentiment_label: str = Field(..., description="Positive, Neutral, or Negative")
    sentiment_strength: str = Field(..., description="Intensity classification")
    compound_score: float = Field(..., description="VADER compound score")
    scores: SentimentScores = Field(..., description="Component VADER scores")
    created_at: str = Field(..., description="ISO 8601 timestamp")


class HistoryListResponse(BaseModel):
    """Paginated collection of reviews retrieved from SQLite."""
    status: str = Field(default="success")
    total: int = Field(..., description="Total matching saved reviews")
    limit: int = Field(..., description="Pagination limit")
    offset: int = Field(..., description="Pagination offset")
    reviews: List[SavedReviewResponse] = Field(..., description="Saved review records")


class HistoryStatsResponse(BaseModel):
    """Summary aggregations for saved reviews stored in SQLite."""
    status: str = Field(default="success")
    total_reviews: int = Field(..., description="Total reviews saved in SQLite")
    text_count: int = Field(..., description="Count of reviews analyzed via Text Analysis")
    url_count: int = Field(..., description="Count of reviews extracted via URL Analysis")
    positive_count: int = Field(..., description="Count of positive reviews")
    neutral_count: int = Field(..., description="Count of neutral reviews")
    negative_count: int = Field(..., description="Count of negative reviews")
    average_compound_score: float = Field(..., description="Average VADER compound score across all saved reviews")

