"""
ReviewLens Data Validation and Sanitization Module
==================================================
Reusable, typed utilities for validating e-commerce review dataset schemas,
ratings, vote counts, text normalization, and SSRF-safe public URL verification.
"""

from __future__ import annotations

import ipaddress
import re
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urlparse

import numpy as np
import pandas as pd

from backend.exceptions import UnsafeUrlError

# Standard required raw dataset schema columns
RAW_SCHEMA_COLUMNS: list[str] = [
    "review_id",
    "product_name",
    "product_category",
    "source",
    "source_url",
    "review_title",
    "review_text",
    "rating",
    "review_date",
    "verified_purchase",
    "helpful_votes",
    "ingestion_timestamp",
    "data_mode",
]

# Standard product categories
VALID_CATEGORIES: set[str] = {
    "Electronics",
    "Home and Kitchen",
    "Beauty and Personal Care",
    "Books",
    "Sports and Outdoors",
}

# Regex patterns for sanitization
WHITESPACE_REGEX = re.compile(r"\s+")
HTML_TAG_REGEX = re.compile(r"<[^>]+>")
URL_REGEX = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)

# Disallowed hostname indicators
DISALLOWED_HOSTS: set[str] = {
    "localhost",
    "localhost.localdomain",
    "broadcasthost",
    "local",
    "0.0.0.0",
    "::",
    "127.0.0.1",
    "::1",
}


def normalize_whitespace(text: str) -> str:
    """
    Collapse repeated whitespace characters into a single space and strip edges.

    Args:
        text: Input string.

    Returns:
        Normalized string with uniform single spaces.
    """
    if not isinstance(text, str):
        return ""
    return WHITESPACE_REGEX.sub(" ", text).strip()


def safe_text(value: Any) -> str:
    """
    Safely convert any value into a sanitized string representation.
    Handles None, NaN, and non-string types cleanly.

    Args:
        value: Any input value.

    Returns:
        Sanitized string or empty string if null/NaN.
    """
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()


def is_valid_review_text(text: Any) -> bool:
    """
    Verify whether a review text is non-empty, non-null, and contains
    meaningful alphanumeric characters.

    Args:
        text: Review text candidate.

    Returns:
        True if text has meaningful content, False otherwise.
    """
    if text is None or pd.isna(text):
        return False
    if not isinstance(text, str):
        text = str(text)
    cleaned = normalize_whitespace(text)
    # Must have at least 2 characters and at least one word character
    return len(cleaned) >= 2 and bool(re.search(r"\w", cleaned))


def validate_rating(value: Any) -> Optional[int]:
    """
    Validate whether a rating value is an integer between 1 and 5 inclusive.

    Args:
        value: Candidate rating value (int, float, str).

    Returns:
        Validated integer rating (1 to 5) or None if invalid.
    """
    if value is None or pd.isna(value):
        return None
    try:
        val_float = float(value)
        if val_float.is_integer() and 1 <= int(val_float) <= 5:
            return int(val_float)
        return None
    except (ValueError, TypeError):
        return None


def validate_non_negative_integer(value: Any) -> Optional[int]:
    """
    Validate whether a value is a non-negative integer (e.g. helpful_votes >= 0).

    Args:
        value: Candidate integer value.

    Returns:
        Validated integer >= 0, or None if invalid.
    """
    if value is None or pd.isna(value):
        return None
    try:
        val_float = float(value)
        if val_float.is_integer() and int(val_float) >= 0:
            return int(val_float)
        return None
    except (ValueError, TypeError):
        return None


def validate_required_columns(
    dataframe: pd.DataFrame, required_columns: list[str]
) -> bool:
    """
    Check if all specified required columns exist in the DataFrame.

    Args:
        dataframe: The pandas DataFrame to validate.
        required_columns: List of expected column names.

    Returns:
        True if all columns are present.

    Raises:
        ValueError: If any required column is missing.
    """
    missing_cols = [col for col in required_columns if col not in dataframe.columns]
    if missing_cols:
        raise ValueError(
            f"Dataset is missing required columns: {missing_cols}. "
            f"Found columns: {list(dataframe.columns)}"
        )
    return True


def sanitize_review_text(text: str) -> str:
    """
    Clean review text by stripping HTML tags, replacing URLs with [URL],
    and normalizing whitespace.

    Args:
        text: Raw review text string.

    Returns:
        Sanitized review text.
    """
    if not isinstance(text, str):
        return ""
    # Remove HTML tags
    cleaned = HTML_TAG_REGEX.sub(" ", text)
    # Replace URL-like fragments with [URL]
    cleaned = URL_REGEX.sub(" [URL] ", cleaned)
    # Normalize whitespace
    return normalize_whitespace(cleaned)


def validate_dataset_schema(dataframe: pd.DataFrame) -> Dict[str, Any]:
    """
    Perform comprehensive validation of dataset schema and basic data integrity.

    Args:
        dataframe: Input pandas DataFrame.

    Returns:
        Dictionary detailing schema validation results, column checks, and row statistics.
    """
    present_columns = list(dataframe.columns)
    missing_columns = [col for col in RAW_SCHEMA_COLUMNS if col not in present_columns]

    total_rows = len(dataframe)
    invalid_ratings_count = 0
    invalid_texts_count = 0

    if "rating" in dataframe.columns:
        invalid_ratings_count = int(
            dataframe["rating"].apply(lambda v: validate_rating(v) is None).sum()
        )

    if "review_text" in dataframe.columns:
        invalid_texts_count = int(
            dataframe["review_text"].apply(lambda v: not is_valid_review_text(v)).sum()
        )

    is_valid = len(missing_columns) == 0

    return {
        "is_valid": is_valid,
        "total_rows": total_rows,
        "present_columns": present_columns,
        "missing_columns": missing_columns,
        "invalid_ratings_count": invalid_ratings_count,
        "invalid_texts_count": invalid_texts_count,
    }


def is_private_or_local_host(hostname: str) -> bool:
    """
    Determine if a given hostname represents a private network, loopback,
    link-local, or unspecified local host (anti-SSRF check).

    Args:
        hostname: Hostname or IP string extracted from URL.

    Returns:
        True if the host is local or private; False if public.
    """
    if not hostname or not isinstance(hostname, str):
        return True

    clean_host = hostname.strip().lower()

    # Direct name matches
    if clean_host in DISALLOWED_HOSTS:
        return True

    # Reserved local domain extensions
    if clean_host.endswith((".local", ".internal", ".localhost", ".localdomain", ".lan")):
        return True

    # Check if host is an IP address
    # Remove brackets for IPv6 literals if present: e.g. [::1] -> ::1
    ip_str = clean_host.strip("[]")
    try:
        ip = ipaddress.ip_address(ip_str)
        return (
            ip.is_loopback
            or ip.is_private
            or ip.is_link_local
            or ip.is_unspecified
            or ip.is_reserved
            or ip.is_multicast
        )
    except ValueError:
        # Not an IP address literal; treated as regular domain name
        pass

    return False


def is_supported_scrape_host(hostname: str, supported_hosts: Set[str]) -> bool:
    """
    Verify whether a hostname matches any entry in the permitted sources allowlist.

    Args:
        hostname: Hostname from URL.
        supported_hosts: Set of permitted host domains.

    Returns:
        True if hostname or parent domain is permitted.
    """
    if not hostname or not supported_hosts:
        return False

    clean_host = hostname.strip().lower()
    if clean_host.startswith("www."):
        clean_host = clean_host[4:]

    for permitted in supported_hosts:
        p = permitted.strip().lower()
        if p.startswith("www."):
            p = p[4:]
        if clean_host == p or clean_host.endswith(f".{p}"):
            return True

    return False


def validate_public_http_url(url: str) -> str:
    """
    Validate that an input string is a safe, non-private, public HTTP/HTTPS URL.
    Protects against SSRF, file access, loopback probing, and protocol abuse.

    Args:
        url: Candidate URL string.

    Returns:
        Validated URL string.

    Raises:
        UnsafeUrlError: If URL is malformed, unsupported scheme, or private host.
    """
    if not url or not isinstance(url, str):
        raise UnsafeUrlError("URL must be a non-empty string.")

    cleaned_url = url.strip()
    if not cleaned_url:
        raise UnsafeUrlError("URL cannot be empty or whitespace-only.")

    try:
        parsed = urlparse(cleaned_url)
    except Exception as exc:
        raise UnsafeUrlError(f"Invalid URL structure: {exc}") from exc

    scheme = (parsed.scheme or "").lower()
    if scheme not in {"http", "https"}:
        raise UnsafeUrlError(
            f"Unsupported URL scheme '{scheme}'. Only http and https protocols are permitted."
        )

    hostname = parsed.hostname
    if not hostname:
        raise UnsafeUrlError("URL does not contain a valid hostname.")

    if is_private_or_local_host(hostname):
        raise UnsafeUrlError(
            f"Access to private, loopback, or local host '{hostname}' is not permitted."
        )

    return cleaned_url
