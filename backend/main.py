"""
ReviewLens Sentiment API - FastAPI Application
==============================================
Production-ready, typed FastAPI service for e-commerce review sentiment intelligence.
Provides local dataset analytics, text-level VADER scoring, and a controlled,
disabled-by-default interface for permitted public review extraction.
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Path as PathParam, Query, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from backend.config import get_settings
from backend.data_service import (
    clean_record_for_json,
    get_category_summaries,
    get_dataset_metadata,
    get_product_summaries,
    get_reviews_paginated,
    get_sentiment_summary,
    get_top_reviews,
    load_enriched_reviews,
)
from backend.exceptions import (
    DatasetNotFoundError,
    DatasetValidationError,
    ReviewLensException,
    ScrapingDisabledError,
    ScrapingFailedError,
    UnsafeUrlError,
    UnsupportedSourceError,
)
from backend.database import (
    clear_all_reviews,
    delete_saved_review,
    get_history_stats,
    get_saved_reviews,
    init_db,
    save_review,
)
from backend.logging_config import get_logger, mask_text_for_logging, sanitize_url_for_logging, setup_logging
from backend.schemas import (
    ApiErrorResponse,
    CategorySummaryResponse,
    HealthResponse,
    HistoryListResponse,
    HistoryStatsResponse,
    PaginatedReviewsResponse,
    ProductSummaryResponse,
    ReviewResponse,
    RootResponse,
    SavedReviewResponse,
    ScrapeAnalyzeRequest,
    ScrapeAnalysisResponse,
    SentimentScores,
    SentimentSummaryResponse,
    SourceInfoResponse,
    TextAnalysisRequest,
    TextAnalysisResponse,
)
from backend.scraper import extract_url_reviews, scrape_permitted_reviews
from backend.sentiment import analyze_review

# Setup logging
setup_logging()
logger = get_logger("main")
settings = get_settings()

# Initialize Rate Limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown events."""
    logger.info("Initializing %s (v%s) in %s mode", settings.APP_NAME, settings.APP_VERSION, settings.ENVIRONMENT)
    try:
        load_enriched_reviews()
        logger.info("Local enriched dataset verified and cached.")
    except Exception as exc:
        logger.warning("Dataset initial cache pre-warming notice: %s", exc)

    try:
        init_db(clear_dummy=True)
        logger.info("SQLite reviews database initialized (zero dummy records).")
    except Exception as db_exc:
        logger.warning("SQLite initialization notice: %s", db_exc)

    yield
    logger.info("Shutting down %s", settings.APP_NAME)


# FastAPI Application Definition
app = FastAPI(
    title="ReviewLens Sentiment API",
    version=settings.APP_VERSION,
    summary="A typed FastAPI service for e-commerce review sentiment analysis using VADER.",
    description=(
        "ReviewLens Sentiment API provides secure, typed endpoints for e-commerce review sentiment intelligence.\n\n"
        "### Key Capabilities:\n"
        "- **VADER Text Scoring**: Fast, deterministic sentiment analysis with 5-tier intensity breakdown.\n"
        "- **Demo Dataset Analytics**: Browsing, filtering, and pagination over enriched e-commerce reviews.\n"
        "- **Product & Category Aggregations**: Precomputed and dynamic multi-dimensional metrics.\n"
        "- **Controlled Web Scraping**: Playwright-ready architecture strictly locked to permitted public domains.\n"
        "- **Anti-SSRF Protections**: Strict rejection of local, private, and loopback IP addresses.\n"
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Attach SlowAPI Limiter
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Accept"],
)



# ==============================================================================
# Global Exception Handlers
# ==============================================================================

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Handle client rate limit violations."""
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "status": "error",
            "message": "Rate limit exceeded. Please slow down your requests.",
            "detail": f"Allowed rate: {settings.RATE_LIMIT_PER_MINUTE} requests per minute.",
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle Pydantic request validation failures with clean JSON error envelope."""
    first_error = exc.errors()[0] if exc.errors() else {}
    msg = first_error.get("msg", "Invalid request body or parameters.")
    loc = " -> ".join(str(l) for l in first_error.get("loc", []))
    detail = f"{loc}: {msg}" if loc else msg
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "error",
            "message": "Request validation failed.",
            "detail": detail,
        },
    )


@app.exception_handler(UnsafeUrlError)
async def unsafe_url_handler(request: Request, exc: UnsafeUrlError) -> JSONResponse:
    """Handle prohibited or insecure URLs."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "status": "error",
            "message": "The provided URL failed security validation.",
            "detail": exc.message,
        },
    )


@app.exception_handler(UnsupportedSourceError)
async def unsupported_source_handler(request: Request, exc: UnsupportedSourceError) -> JSONResponse:
    """Handle scraping requests to unpermitted hosts."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "status": "error",
            "message": "The requested review source is not supported.",
            "detail": exc.message,
        },
    )


@app.exception_handler(ScrapingDisabledError)
async def scraping_disabled_handler(request: Request, exc: ScrapingDisabledError) -> JSONResponse:
    """Handle scrape requests when Playwright is toggled off."""
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "status": "error",
            "message": exc.message,
            "detail": None,
        },
    )


@app.exception_handler(ScrapingFailedError)
async def scraping_failed_handler(request: Request, exc: ScrapingFailedError) -> JSONResponse:
    """Handle runtime extraction failures."""
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={
            "status": "error",
            "message": "Review extraction could not be completed.",
            "detail": exc.message,
        },
    )


@app.exception_handler(DatasetNotFoundError)
async def dataset_not_found_handler(request: Request, exc: DatasetNotFoundError) -> JSONResponse:
    """Handle missing processed dataset."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "status": "error",
            "message": "Local dataset not found.",
            "detail": exc.message,
        },
    )


@app.exception_handler(DatasetValidationError)
async def dataset_validation_handler(request: Request, exc: DatasetValidationError) -> JSONResponse:
    """Handle corrupted or invalid dataset schema."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "message": "Dataset integrity validation failed.",
            "detail": exc.message,
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Ensure consistent formatting for generic HTTP exceptions."""
    detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": detail,
            "detail": None,
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Prevent unhandled traceback leakage to public API consumers."""
    logger.error("Unhandled internal error: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "message": "An internal server error occurred while processing your request.",
            "detail": None,
        },
    )


# ==============================================================================
# Endpoint 1: System Index
# ==============================================================================

@app.get(
    "/",
    tags=["System"],
    response_model=RootResponse,
    summary="API Welcome & Index",
    description="Returns welcome status and links to documentation and health check.",
)
async def get_index() -> RootResponse:
    return RootResponse(
        status="success",
        message="Welcome to ReviewLens Sentiment API",
        docs_url="/docs",
        health_url="/health",
        api_version="v1",
    )


@app.get("/favicon.ico", include_in_schema=False)
async def get_favicon() -> Response:
    """Silently acknowledge browser tab favicon requests without 404 logs."""
    return Response(status_code=status.HTTP_204_NO_CONTENT)



# ==============================================================================
# Endpoint 2: Health Check
# ==============================================================================

@app.get(
    "/health",
    tags=["System"],
    response_model=HealthResponse,
    summary="Service Health Check",
    description="Returns service availability, app name, version, and running environment.",
)
async def get_health() -> HealthResponse:
    return HealthResponse(
        status="healthy",
        service=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
    )


# ==============================================================================
# Endpoint 3: Dataset Provenance & Capabilities
# ==============================================================================

@app.get(
    "/api/v1/info",
    tags=["System"],
    response_model=SourceInfoResponse,
    summary="Dataset Info & Features",
    description="Returns active data mode, relative dataset path, review counts, and feature flags.",
)
async def get_info() -> SourceInfoResponse:
    metadata = get_dataset_metadata()
    return SourceInfoResponse(**metadata)


# ==============================================================================
# Endpoint 4: Text Sentiment Analysis
# ==============================================================================

@app.post(
    "/api/v1/analyze/text",
    tags=["Sentiment Analysis"],
    response_model=TextAnalysisResponse,
    summary="Analyze Review Text Sentiment",
    description="Scores a single text string using VADER and returns label, 5-tier intensity, and valence scores.",
)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def analyze_text(request: Request, body: TextAnalysisRequest) -> TextAnalysisResponse:
    logger.info("Analyzing text sentiment: %s", mask_text_for_logging(body.text))
    result = analyze_review(body.text)
    scores = SentimentScores(
        neg=result["vader_neg"],
        neu=result["vader_neu"],
        pos=result["vader_pos"],
        compound=result["compound_score"],
    )

    saved_id: Optional[int] = None
    try:
        saved_rec = save_review(
            review_text=body.text,
            sentiment_label=result["sentiment_label"],
            sentiment_strength=result["sentiment_strength"],
            compound_score=result["compound_score"],
            vader_pos=result["vader_pos"],
            vader_neu=result["vader_neu"],
            vader_neg=result["vader_neg"],
            source_type="text",
            product_name="Text Analysis Input",
            product_category="Custom Text",
        )
        saved_id = saved_rec["id"]
    except Exception as save_err:
        logger.warning("Failed to auto-persist review to SQLite: %s", save_err)

    return TextAnalysisResponse(
        status="success",
        text=body.text,
        sentiment_label=result["sentiment_label"],
        sentiment_strength=result["sentiment_strength"],
        scores=scores,
        saved_id=saved_id,
    )


# ==============================================================================
# Endpoint 5: Demo Sentiment Summary
# ==============================================================================

@app.get(
    "/api/v1/demo/summary",
    tags=["Demo Data"],
    response_model=SentimentSummaryResponse,
    summary="Dataset Sentiment Summary Metrics",
    description="Returns overall sentiment distribution, percentages, average ratings, and compound scores.",
)
async def get_demo_summary() -> SentimentSummaryResponse:
    summary_data = get_sentiment_summary()
    return SentimentSummaryResponse(**summary_data)


# ==============================================================================
# Endpoint 6: Demo Paginated & Filtered Reviews
# ==============================================================================

@app.get(
    "/api/v1/demo/reviews",
    tags=["Demo Data"],
    response_model=PaginatedReviewsResponse,
    summary="Browse & Filter Enriched Reviews",
    description="Paginated retrieval of enriched reviews with optional sentiment, category, and product filters.",
)
async def get_demo_reviews(
    limit: int = Query(default=20, ge=1, le=100, description="Page record limit"),
    offset: int = Query(default=0, ge=0, description="Page record offset"),
    sentiment: Optional[str] = Query(default=None, description="Filter by sentiment label (Positive, Neutral, Negative)"),
    category: Optional[str] = Query(default=None, description="Filter by product category"),
    product: Optional[str] = Query(default=None, description="Filter by product name substring"),
) -> PaginatedReviewsResponse:
    total, paginated_df = get_reviews_paginated(
        limit=limit,
        offset=offset,
        sentiment=sentiment,
        category=category,
        product=product,
    )

    review_records = [
        ReviewResponse(**clean_record_for_json(row))
        for row in paginated_df.to_dict(orient="records")
    ]

    return PaginatedReviewsResponse(
        status="success",
        total=total,
        limit=limit,
        offset=offset,
        reviews=review_records,
    )


# ==============================================================================
# Endpoint 7: Product Sentiment Analytics
# ==============================================================================

@app.get(
    "/api/v1/analytics/products",
    tags=["Dataset Analytics"],
    response_model=List[ProductSummaryResponse],
    summary="Product-Level Sentiment Analytics",
    description="Aggregated sentiment breakdown, average ratings, and review volume per product.",
)
async def get_products_analytics() -> List[ProductSummaryResponse]:
    summaries = get_product_summaries()
    return [ProductSummaryResponse(**item) for item in summaries]


# ==============================================================================
# Endpoint 8: Category Sentiment Analytics
# ==============================================================================

@app.get(
    "/api/v1/analytics/categories",
    tags=["Dataset Analytics"],
    response_model=List[CategorySummaryResponse],
    summary="Category-Level Sentiment Analytics",
    description="Aggregated sentiment breakdown, average ratings, and review volume per product category.",
)
async def get_categories_analytics() -> List[CategorySummaryResponse]:
    summaries = get_category_summaries()
    return [CategorySummaryResponse(**item) for item in summaries]


# ==============================================================================
# Endpoint 9: Top Reviews by Sentiment
# ==============================================================================

@app.get(
    "/api/v1/demo/top-reviews/{sentiment}",
    tags=["Demo Data"],
    response_model=List[ReviewResponse],
    summary="Retrieve Top Positive or Negative Reviews",
    description="Returns highest compound score reviews for Positive, or lowest compound score for Negative.",
)
async def get_top_reviews_endpoint(
    sentiment: str = PathParam(..., description="Sentiment category: 'Positive' or 'Negative'"),
    limit: int = Query(default=10, ge=1, le=25, description="Number of reviews to return"),
) -> List[ReviewResponse]:
    norm = sentiment.strip().title()
    if norm not in {"Positive", "Negative"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Sentiment must be 'Positive' or 'Negative'. Received: '{sentiment}'",
        )

    try:
        df_top = get_top_reviews(norm, limit=limit)
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err)) from val_err

    review_records = [
        ReviewResponse(**clean_record_for_json(row))
        for row in df_top.to_dict(orient="records")
    ]
    return review_records


# ==============================================================================
# Endpoint 10: URL Review Extraction & Analysis
# ==============================================================================

@app.post(
    "/api/v1/analyze/url",
    tags=["Scraping"],
    response_model=ScrapeAnalysisResponse,
    summary="Extract & Analyze Reviews from Permitted URL",
    description=(
        "Resilient review extraction endpoint supporting Amazon, Flipkart, and public e-commerce URLs.\n\n"
        "Extracts customer reviews, runs VADER scoring, and automatically persists them into SQLite."
    ),
)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def analyze_url(request: Request, body: ScrapeAnalyzeRequest) -> ScrapeAnalysisResponse:
    logger.info("Received scrape analysis request for: %s", sanitize_url_for_logging(body.url))

    # Run extraction via worker thread to avoid blocking the event loop
    result = await asyncio.to_thread(extract_url_reviews, body.url, max_reviews=body.max_reviews)

    return ScrapeAnalysisResponse(
        status=result["status"],
        message=result["message"],
        source_url=result["source_url"],
        page_title=result.get("page_title"),
        meta_description=result.get("meta_description"),
        hostname=result.get("hostname"),
        total=result["total"],
        saved_to_db=result.get("saved_to_db", False),
        average_compound_score=result.get("average_compound_score"),
        positive_percentage=result.get("positive_percentage"),
        neutral_percentage=result.get("neutral_percentage"),
        negative_percentage=result.get("negative_percentage"),
        reviews=[TextAnalysisResponse(**r) for r in result.get("reviews", [])],
    )


# ==============================================================================
# Endpoint 11: Saved Reviews History (SQLite)
# ==============================================================================

@app.get(
    "/api/v1/history",
    tags=["History"],
    response_model=HistoryListResponse,
    summary="Query Saved Reviews from SQLite",
    description="Returns filtered, paginated list of real user-analyzed text and URL reviews.",
)
async def get_history_endpoint(
    source_type: Optional[str] = Query(default=None, description="Filter by 'text', 'url', or 'all'"),
    sentiment: Optional[str] = Query(default=None, description="Filter by 'Positive', 'Neutral', 'Negative', or 'all'"),
    search: Optional[str] = Query(default=None, description="Keyword search in review body, title, or product"),
    limit: int = Query(default=50, ge=1, le=200, description="Page item limit"),
    offset: int = Query(default=0, ge=0, description="Page offset"),
) -> HistoryListResponse:
    res = get_saved_reviews(
        source_type=source_type,
        sentiment=sentiment,
        search=search,
        limit=limit,
        offset=offset,
    )
    return HistoryListResponse(
        status="success",
        total=res["total"],
        limit=res["limit"],
        offset=res["offset"],
        reviews=[SavedReviewResponse(**r) for r in res["reviews"]],
    )


# ==============================================================================
# Endpoint 12: Saved Reviews Statistics (SQLite)
# ==============================================================================

@app.get(
    "/api/v1/history/stats",
    tags=["History"],
    response_model=HistoryStatsResponse,
    summary="Summary Statistics of Saved Reviews in SQLite",
    description="Returns counts by source, sentiment breakdown, and average compound score.",
)
async def get_history_stats_endpoint() -> HistoryStatsResponse:
    stats = get_history_stats()
    return HistoryStatsResponse(
        status="success",
        total_reviews=stats["total_reviews"],
        text_count=stats["text_count"],
        url_count=stats["url_count"],
        positive_count=stats["positive_count"],
        neutral_count=stats["neutral_count"],
        negative_count=stats["negative_count"],
        average_compound_score=stats["average_compound_score"],
    )


# ==============================================================================
# Endpoint 13: Delete Saved Review (SQLite)
# ==============================================================================

@app.delete(
    "/api/v1/history/{review_id}",
    tags=["History"],
    summary="Delete a Saved Review",
    description="Removes a specific review record from SQLite by ID.",
)
async def delete_history_item(
    review_id: int = PathParam(..., description="Unique database row ID to delete"),
) -> Dict[str, Any]:
    success = delete_saved_review(review_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review with ID {review_id} not found in database.",
        )
    return {"status": "success", "message": f"Review {review_id} deleted successfully."}


# ==============================================================================
# Endpoint 14: Clear All Saved Reviews (SQLite)
# ==============================================================================

@app.delete(
    "/api/v1/history",
    tags=["History"],
    summary="Clear All Saved Reviews",
    description="Removes all saved reviews from the SQLite database.",
)
async def clear_history_endpoint() -> Dict[str, Any]:
    count = clear_all_reviews()
    return {"status": "success", "message": f"Cleared {count} reviews from database."}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host=settings.HOST, port=settings.PORT, reload=True)


