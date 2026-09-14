"""
End-to-end smoke test for Gorilla Glass URL review extraction, VADER scoring, and SQLite persistence.
"""

from fastapi.testclient import TestClient
from backend.main import app
from backend.database import get_saved_reviews, get_history_stats

def run_smoke_test():
    client = TestClient(app)
    
    # 1. Health check
    h = client.get("/health")
    assert h.status_code == 200, f"Health check failed: {h.text}"
    print("[OK] Health check PASSED")
    
    # 2. Extract Gorilla Glass reviews via API endpoint
    target_url = "https://www.amazon.in/POPIO-Military-Grade-iPhone-Anti-Scratch-Bubble-Free/dp/B0CG29HWSS/"
    payload = {"url": target_url, "max_reviews": 10, "preview": False}
    
    print(f"Sending POST /api/v1/analyze/url for: {target_url}")
    resp = client.post("/api/v1/analyze/url", json=payload)
    assert resp.status_code == 200, f"Analyze URL failed: {resp.status_code} {resp.text}"
    
    data = resp.json()
    assert data["status"] == "success"
    assert data["total"] > 0
    print(f"[OK] Extracted {data['total']} reviews.")
    print(f"[OK] Page title: {data.get('page_title')}")
    
    # Check reviews text
    reviews = data["reviews"]
    all_texts = " ".join([r["text"] for r in reviews]).lower()
    
    # Check that Bluetooth headphone text is absent
    assert "bluetooth 5.3" not in all_texts, "ERROR: Static Bluetooth headphone review was returned!"
    assert "battery life beyond 36 hours" not in all_texts, "ERROR: Headphone battery review was returned!"
    print("[OK] Verified ZERO headphone hallucination / static text.")
    
    # Check that glass / screen protection context is present
    glass_signals = ["glass", "screen", "tempered", "scratch", "bubble", "protection", "clarity", "popio"]
    found_signals = [s for s in glass_signals if s in all_texts]
    assert len(found_signals) > 0, f"Expected glass review indicators, found none in: {all_texts[:300]}"
    print(f"[OK] Verified Gorilla Glass context signals: {found_signals}")
    
    # Check reviews structure
    for idx, r in enumerate(reviews[:3]):
        print(f"   Review {idx+1}: [{r['sentiment_label']}] {r['text'][:110]}...")
        assert r["sentiment_label"] in ["Positive", "Neutral", "Negative"]
        assert "scores" in r
        assert "compound" in r["scores"]
    print("[OK] VADER sentiment scoring structure verified.")
    
    # 3. Check SQLite persistence
    db_history = get_saved_reviews(source_type="url", limit=10)
    assert db_history["total"] > 0
    matched_urls = [row["source_url"] for row in db_history["reviews"] if row.get("source_url") == target_url]
    assert len(matched_urls) > 0, f"Target URL not found in SQLite history: {db_history}"
    print(f"[OK] Verified SQLite persistence: found {len(matched_urls)} reviews saved for this URL in data/reviewlens.db.")
    
    stats = get_history_stats()
    print(f"[OK] SQLite Stats: total={stats['total_reviews']}, url_count={stats['url_count']}, avg_compound={stats['average_compound_score']}")
    print("\n========================================================")
    print("ALL SMOKE TESTS PASSED 100% PERFECTLY!")
    print("========================================================")

if __name__ == "__main__":
    run_smoke_test()
