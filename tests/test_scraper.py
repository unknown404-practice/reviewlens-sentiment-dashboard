"""
Unit and regression tests for Web Review Scraper and Extraction Engine.
Guarantees product context fidelity: Gorilla Glass links must extract screen protection reviews,
NEVER static Bluetooth headphone text.
"""

import pytest
from backend.scraper import extract_url_reviews


def test_gorilla_glass_url_does_not_return_bluetooth_headphone_reviews():
    url = "https://www.amazon.in/POPIO-Military-Grade-iPhone-Anti-Scratch-Bubble-Free/dp/B0CG29HWSS/"
    result = extract_url_reviews(url, max_reviews=10)

    assert result["status"] == "success"
    assert len(result["reviews"]) > 0

    all_texts = " ".join([r["text"] for r in result["reviews"]]).lower()

    # MUST NOT contain headphone hallucination / static fallback
    assert "bluetooth 5.3" not in all_texts, "Scraper hallucinated Bluetooth 5.3 headphone review for Gorilla Glass!"
    assert "battery life beyond 36 hours" not in all_texts, "Scraper hallucinated headphone battery life for Gorilla Glass!"
    assert "charging cable defective" not in all_texts, "Scraper hallucinated headphone charging cable for Gorilla Glass!"

    # MUST reflect actual product category (glass, screen protector, tempered, scratch, clarity, popio)
    glass_indicators = ["glass", "screen", "tempered", "scratch", "bubble", "protection", "clarity", "popio"]
    found_indicator = any(indicator in all_texts for indicator in glass_indicators)
    assert found_indicator, f"Expected review text to mention screen/glass protection attributes. Got:\n{all_texts[:300]}"


def test_amazon_opentech_gorilla_glass_context():
    url = "https://www.amazon.in/OpenTech-Military-Grade-Compatible-15-Installation/dp/B0CJ17HHHD/"
    result = extract_url_reviews(url, max_reviews=10)

    assert result["status"] == "success"
    all_texts = " ".join([r["text"] for r in result["reviews"]]).lower()

    assert "bluetooth" not in all_texts
    assert "headphone" not in all_texts


def test_condom_review_permalink_returns_auth_required_and_no_mock_hallucination():
    """
    Amazon standalone customer review permalinks (e.g. /portal/customer-reviews/srp/-/R5PDGEC552AMV)
    are restricted behind account login (/ap/signin).
    The scraper MUST return status='auth_required' with zero fake reviews and zero SQLite persistence.
    """
    url = "https://www.amazon.in/portal/customer-reviews/srp/-/R5PDGEC552AMV/ref=cm_cr_dp_d_rvw_ttl?_encoding=UTF8&ie=UTF8"
    result = extract_url_reviews(url, max_reviews=10)

    assert result["status"] == "auth_required"
    assert result["saved_to_db"] is False
    assert result["total"] == 0
    assert len(result["reviews"]) == 0
    assert "R5PDGEC552AMV" in result["message"]
    assert "/ap/signin" in result["message"] or "login" in result["message"].lower()
    assert "/dp/<ASIN>" in result["message"]

    # Verify no fake reviews saved in SQLite
    from backend.database import get_db_connection
    conn = get_db_connection()
    try:
        rows = conn.execute(
            "SELECT COUNT(*) FROM saved_reviews WHERE review_text LIKE '%R5PDGEC552AMV%' OR product_name = 'Customer Reviews'"
        ).fetchone()
        assert rows[0] == 0, f"Found {rows[0]} synthetic records in SQLite!"
    finally:
        conn.close()


def test_product_reviews_url_normalization():
    """Verify that Amazon review URLs with ASINs are rewritten to public detail pages."""
    from backend.scraper import extract_amazon_asin, extract_amazon_review_id, normalize_amazon_url

    # Product reviews path -> /dp/
    raw_url = "https://www.amazon.in/POPIO-Screen-Protector/product-reviews/B0CG29HWSS/ref=cm_cr_dp_d_show_all_btm"
    normalized = normalize_amazon_url(raw_url)
    assert normalized == "https://www.amazon.in/dp/B0CG29HWSS"

    # ASIN extraction
    assert extract_amazon_asin("https://www.amazon.in/dp/B0CG29HWSS/") == "B0CG29HWSS"
    assert extract_amazon_asin("https://www.amazon.com/gp/product/B08L5VJYV7") == "B08L5VJYV7"

    # Review permalink ID extraction
    assert (
        extract_amazon_review_id(
            "https://www.amazon.in/portal/customer-reviews/srp/-/R5PDGEC552AMV/ref=cm_cr_dp_d_rvw_ttl"
        )
        == "R5PDGEC552AMV"
    )
    assert extract_amazon_review_id("https://www.amazon.in/gp/customer-reviews/R3581SGYOL4O8C") == "R3581SGYOL4O8C"


def test_routing_blacklist_and_product_name_derivation():
    """Verify routing segments are blacklisted and double title suffixing is prevented."""
    from backend.scraper import _clean_product_title, _derive_product_metadata

    # Never derive "Customer Reviews" or routing segments as product name
    prod_name, cat = _derive_product_metadata(
        "https://www.amazon.in/portal/customer-reviews/srp/-/R5PDGEC552AMV",
        "Customer Reviews - Customer Reviews",
    )
    assert prod_name != "Customer Reviews"
    assert "Customer Reviews - Customer Reviews" not in prod_name
    assert "portal" not in prod_name.lower()
    assert "srp" not in prod_name.lower()

    # Retailer title cleaning
    cleaned = _clean_product_title("Amazon.in: Customer reviews: Durex Extra Thin Condoms", "www.amazon.in")
    assert cleaned == "Durex Extra Thin Condoms"


def test_sexual_wellness_contraceptives_category_and_reviews():
    """Verify Sexual Wellness & Contraceptives category detection and domain attributes."""
    from backend.scraper import _derive_product_metadata, _generate_contextual_reviews

    name1, cat1 = _derive_product_metadata("https://www.amazon.in/Durex-Extra-Thin-Condoms-Pack/dp/B00N2P39TY", None)
    assert cat1 == "Sexual Wellness & Contraceptives"

    name2, cat2 = _derive_product_metadata("https://www.amazon.in/Manforce-Staylong-Condoms-Flavoured-10s/dp/B010GCSLMS", None)
    assert cat2 == "Sexual Wellness & Contraceptives"

    # Contextual reviews must not contain "Verified Purchase" or "Verified Buyer"
    reviews = _generate_contextual_reviews("Durex Thin Condoms", "Sexual Wellness & Contraceptives", "B00N2P39TY", max_reviews=5)
    assert len(reviews) > 0

    all_rev_text = " ".join([r["text"] for r in reviews]).lower()
    assert "verified purchase" not in all_rev_text
    assert "verified buyer" not in all_rev_text

    # Domain attributes must be present
    wellness_indicators = ["discreet packaging", "sensitivity", "durability", "comfort", "latex"]
    assert any(ind in all_rev_text for ind in wellness_indicators)


def test_contextual_reviews_never_contain_verified_purchase_labels():
    """Verify that generated contextual reviews across all categories NEVER label reviews as Verified Purchase or Verified Buyer."""
    from backend.scraper import _generate_contextual_reviews

    categories = [
        "Sexual Wellness & Contraceptives",
        "Screen Protectors & Tempered Glass",
        "Cases & Mobile Protection",
        "Footwear & Apparel",
        "Audio & Acoustics",
        "Consumer Goods & Electronics",
    ]

    for cat in categories:
        reviews = _generate_contextual_reviews("Test Item", cat, "REF12345", max_reviews=8)
        assert len(reviews) > 0
        for r in reviews:
            txt = r["text"].lower()
            author = r["author"].lower()
            assert "verified purchase" not in txt, f"Found 'Verified Purchase' in category {cat}: {r['text']}"
            assert "verified review" not in txt, f"Found 'Verified Review' in category {cat}: {r['text']}"
            assert "verified buyer" not in author, f"Found 'Verified Buyer' author in category {cat}: {author}"
            assert "verified customer" not in author, f"Found 'Verified Customer' author in category {cat}: {author}"


def test_standard_review_path_permalink_and_asin_query_params():
    """Verify /review/<REVIEW_ID> permalinks and ASIN query parameters."""
    from backend.scraper import extract_amazon_asin, extract_amazon_review_id, normalize_amazon_url

    # /review/<ID> pattern
    assert extract_amazon_review_id("https://www.amazon.in/review/R5PDGEC552AMV") == "R5PDGEC552AMV"
    assert extract_amazon_review_id("https://www.amazon.com/review/R5PDGEC552AMV/ref=cm_cr") == "R5PDGEC552AMV"
    assert extract_amazon_review_id("https://www.amazon.com/gp/review/R5PDGEC552AMV") == "R5PDGEC552AMV"

    # Query param ASIN extraction
    assert extract_amazon_asin("https://www.amazon.in/portal/customer-reviews/srp/-/R5PDGEC552AMV?asin=B0CG29HWSS") == "B0CG29HWSS"
    assert extract_amazon_asin("https://www.amazon.in/review/R5PDGEC552AMV?ref=xyz&ASIN=B00N2P39TY") == "B00N2P39TY"

    # Normalizing URL containing ASIN query param rewrites to /dp/<ASIN>
    normalized = normalize_amazon_url("https://www.amazon.in/portal/customer-reviews/srp/-/R5PDGEC552AMV?asin=B0CG29HWSS")
    assert normalized == "https://www.amazon.in/dp/B0CG29HWSS"


def test_opaque_ids_never_become_slug_product_names():
    """Verify opaque review IDs and ASINs never become product names."""
    from backend.scraper import _derive_product_metadata

    # Review permalink path without title
    name1, cat1 = _derive_product_metadata("https://www.amazon.in/review/R5PDGEC552AMV", None)
    assert name1 == "Amazon Review (R5PDGEC552AMV)"
    assert name1 != "R5Pdgec552Amv"
    assert name1 != "Customer Reviews"

    # ASIN path without title
    name2, cat2 = _derive_product_metadata("https://www.amazon.in/dp/B0CG29HWSS", None)
    assert name2 == "Amazon Product (B0CG29HWSS)"
    assert name2 != "B0Cg29Hwss"


def test_auth_walled_permalinks_never_saved_to_sqlite():
    """Verify that scrape failures on review permalinks (/review/ or /portal/) never write records to SQLite saved_reviews."""
    from backend.database import get_db_connection
    from backend.scraper import extract_url_reviews

    conn = get_db_connection()
    try:
        initial_count = conn.execute("SELECT COUNT(*) FROM saved_reviews").fetchone()[0]
    finally:
        conn.close()

    # Call extract_url_reviews on a standalone review permalink
    res = extract_url_reviews("https://www.amazon.in/review/R5PDGEC552AMV", max_reviews=5)

    assert res["status"] == "auth_required"
    assert res["saved_to_db"] is False
    assert res["total"] == 0
    assert len(res["reviews"]) == 0

    conn = get_db_connection()
    try:
        final_count = conn.execute("SELECT COUNT(*) FROM saved_reviews").fetchone()[0]
        assert final_count == initial_count, f"Records were written to SQLite! Count went from {initial_count} to {final_count}"
    finally:
        conn.close()

