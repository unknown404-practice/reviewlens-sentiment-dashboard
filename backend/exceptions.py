"""
ReviewLens Custom Domain Exceptions
===================================
Custom exception hierarchy for clean error categorization and handling.
Avoid exposing internal tracebacks or exception class details to public clients.
"""

from __future__ import annotations


class ReviewLensException(Exception):
    """Base exception for all ReviewLens backend errors."""

    def __init__(self, message: str, detail: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.detail = detail


class DatasetNotFoundError(ReviewLensException):
    """Raised when the expected dataset CSV file is missing or unreadable."""
    pass


class DatasetValidationError(ReviewLensException):
    """Raised when dataset fails schema, column, or integrity validation."""
    pass


class UnsupportedSourceError(ReviewLensException):
    """Raised when a review source or URL domain is not supported."""
    pass


class ScrapingDisabledError(ReviewLensException):
    """Raised when live scraping is requested but disabled via configuration."""
    pass


class ScrapingFailedError(ReviewLensException):
    """Raised when review extraction fails or encounters runtime issues."""
    pass


class UnsafeUrlError(ReviewLensException):
    """Raised when an unsafe, non-HTTP, loopback, or private URL is submitted."""
    pass
