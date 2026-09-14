"""
ReviewLens URL and Data Validation Unit Tests
=============================================
Verifies URL safety checks, SSRF mitigation, IP address rejection,
and dataset validator utilities.
"""

import pytest

from backend.exceptions import UnsafeUrlError
from backend.validators import (
    is_private_or_local_host,
    is_supported_scrape_host,
    validate_public_http_url,
)


class TestUrlValidation:
    """Test suite for anti-SSRF and public URL validation."""

    def test_valid_https_url(self):
        """Verify normal public HTTPS URL passes validation."""
        url = "https://example.com/products/item-1"
        assert validate_public_http_url(url) == url

    def test_valid_http_url(self):
        """Verify normal public HTTP URL passes validation."""
        url = "http://example.com/catalog"
        assert validate_public_http_url(url) == url

    def test_blank_url_rejection(self):
        """Verify empty and whitespace-only URLs are rejected."""
        with pytest.raises(UnsafeUrlError, match="URL must be a non-empty string|cannot be empty"):
            validate_public_http_url("")

        with pytest.raises(UnsafeUrlError, match="cannot be empty"):
            validate_public_http_url("   ")

    def test_file_url_rejection(self):
        """Verify file:// scheme is rejected."""
        with pytest.raises(UnsafeUrlError, match="Unsupported URL scheme"):
            validate_public_http_url("file:///etc/passwd")

    def test_javascript_url_rejection(self):
        """Verify javascript: pseudo-protocol is rejected."""
        with pytest.raises(UnsafeUrlError, match="Unsupported URL scheme"):
            validate_public_http_url("javascript:alert(1)")

    def test_ftp_url_rejection(self):
        """Verify ftp:// scheme is rejected."""
        with pytest.raises(UnsafeUrlError, match="Unsupported URL scheme"):
            validate_public_http_url("ftp://example.com/data.txt")

    def test_localhost_rejection(self):
        """Verify localhost domain name is rejected."""
        with pytest.raises(UnsafeUrlError, match="private, loopback, or local host"):
            validate_public_http_url("http://localhost:8000/api")

        with pytest.raises(UnsafeUrlError, match="private, loopback, or local host"):
            validate_public_http_url("http://localhost.localdomain/test")

    def test_loopback_ip_rejection(self):
        """Verify IPv4 and IPv6 loopback addresses are rejected."""
        with pytest.raises(UnsafeUrlError, match="private, loopback, or local host"):
            validate_public_http_url("http://127.0.0.1:8000")

        with pytest.raises(UnsafeUrlError, match="private, loopback, or local host"):
            validate_public_http_url("http://127.0.0.2:3000")

        with pytest.raises(UnsafeUrlError, match="private, loopback, or local host"):
            validate_public_http_url("http://[::1]:8000")

    def test_private_ip_rejection(self):
        """Verify RFC 1918 private IPv4 addresses are rejected."""
        with pytest.raises(UnsafeUrlError, match="private, loopback, or local host"):
            validate_public_http_url("http://192.168.1.1/admin")

        with pytest.raises(UnsafeUrlError, match="private, loopback, or local host"):
            validate_public_http_url("http://10.0.0.15/dashboard")

        with pytest.raises(UnsafeUrlError, match="private, loopback, or local host"):
            validate_public_http_url("http://172.16.0.50:5000")

    def test_link_local_and_unspecified_ip_rejection(self):
        """Verify link-local (e.g. AWS metadata 169.254.169.254) and unspecified IPs are rejected."""
        with pytest.raises(UnsafeUrlError, match="private, loopback, or local host"):
            validate_public_http_url("http://169.254.169.254/latest/meta-data")

        with pytest.raises(UnsafeUrlError, match="private, loopback, or local host"):
            validate_public_http_url("http://0.0.0.0:8080")

    def test_malformed_url_rejection(self):
        """Verify URLs missing hostnames or with invalid syntax are rejected."""
        with pytest.raises(UnsafeUrlError, match="valid hostname"):
            validate_public_http_url("https://")

        with pytest.raises(UnsafeUrlError, match="valid hostname"):
            validate_public_http_url("http:///just-path")

    def test_is_private_or_local_host(self):
        """Direct tests for host identification."""
        assert is_private_or_local_host("localhost") is True
        assert is_private_or_local_host("127.0.0.1") is True
        assert is_private_or_local_host("192.168.0.1") is True
        assert is_private_or_local_host("10.10.10.10") is True
        assert is_private_or_local_host("172.20.1.1") is True
        assert is_private_or_local_host("169.254.1.1") is True
        assert is_private_or_local_host("app.local") is True
        assert is_private_or_local_host("service.internal") is True

        assert is_private_or_local_host("example.com") is False
        assert is_private_or_local_host("public-store.org") is False
        assert is_private_or_local_host("8.8.8.8") is False

    def test_is_supported_scrape_host(self):
        """Test permitted scraping host allowlist matching."""
        supported = {"example.com", "my-public-shop.org"}
        assert is_supported_scrape_host("example.com", supported) is True
        assert is_supported_scrape_host("www.example.com", supported) is True
        assert is_supported_scrape_host("reviews.example.com", supported) is True
        assert is_supported_scrape_host("my-public-shop.org", supported) is True

        # Unsupported hosts
        assert is_supported_scrape_host("amazon.com", supported) is False
        assert is_supported_scrape_host("evil.com", supported) is False
        assert is_supported_scrape_host("another-example.com", supported) is False
