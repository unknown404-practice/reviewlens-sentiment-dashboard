"""
ReviewLens Logging Configuration Module
=======================================
Configures structured, privacy-preserving, and console-friendly logging for Windows.
Ensures full review text and sensitive query parameters are never logged.
"""

from __future__ import annotations

import logging
import sys
from urllib.parse import urlparse

from backend.config import get_settings


def sanitize_url_for_logging(url: str) -> str:
    """
    Sanitize a URL for log output, keeping only scheme and host, omitting query strings or paths.

    Args:
        url: Input URL string.

    Returns:
        Sanitized representation, e.g., 'https://example.com'
    """
    if not url:
        return "<empty-url>"
    try:
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}" if parsed.netloc else "<invalid-url>"
    except Exception:
        return "<malformed-url>"


def mask_text_for_logging(text: str, max_chars: int = 30) -> str:
    """
    Create a truncated and safe preview of user text for logging without storing or exposing full content.

    Args:
        text: Input review text.
        max_chars: Number of preview characters.

    Returns:
        Safe preview string including length metadata.
    """
    if not text:
        return "<empty-text>"
    length = len(text)
    preview = text[:max_chars].replace("\n", " ").replace("\r", " ").strip()
    return f"[length={length} chars, preview='{preview}...']"


def setup_logging() -> logging.Logger:
    """
    Configure the root logger and standard handlers based on application settings.

    Returns:
        The configured application logger.
    """
    settings = get_settings()
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    log_format = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    logging.basicConfig(
        level=log_level,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
        force=True,
    )

    logger = logging.getLogger("reviewlens")
    logger.setLevel(log_level)
    return logger


def get_logger(name: str = "reviewlens") -> logging.Logger:
    """
    Retrieve a named logger under the reviewlens hierarchy.

    Args:
        name: Logger name suffix or full name.

    Returns:
        Standard logging.Logger instance.
    """
    if name.startswith("reviewlens"):
        return logging.getLogger(name)
    return logging.getLogger(f"reviewlens.{name}")
