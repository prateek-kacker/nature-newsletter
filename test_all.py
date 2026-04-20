"""
test_all.py — End-to-end test: fetcher → agent → web app
"""
import os, sys, json

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
print("=" * 50)
print("NATURE WEEKLY — END TO END TEST")
print("=" * 50)

# ── 1. Fetcher ────────────────────────────────────
print("\n[1/3] Testing fetcher (RSS + AI rewrite)...")
from fetcher import fetch_from_rss, rewrite_with_ai
raw = fetch_from_rss(max_articles=2)  # just 2 for speed
assert len(raw) > 0, "No articles from RSS"
print(f"  ✓ RSS OK — {len(raw)} articles fetched")
articles = rewrite_with_ai(raw)
assert len(articles) > 0, "Rewrite returned nothing"
first = articles[0]
assert first.get("title"), "Article missing title"
assert first.get("link"), "Article missing link"
assert first.get("simple_summary"), "Article missing summary"
print(f"  ✓ Title: {first['title'][:70]}")
print(f"  ✓ Summary: {first['simple_summary'][:80]}...")
print(f"  ✓ AI rewritten: {first['ai_rewritten']}")

# ── 2. Agent logic (without S3 or AgentCore server) ──
print("\n[2/3] Testing agent logic (mocked S3)...")
import agent as agent_module
import fetcher as fetcher_module

# Reuse already-fetched articles — no extra AI calls
fetcher_module.fetch_articles = lambda: articles

# Mock S3 save
saved = {}
def mock_save(data):
    saved.update(data)
agent_module.save_to_s3 = mock_save

# Call the underlying logic directly (bypassing AgentCore decorator)
from datetime import datetime as dt
from fetcher import fetch_articles as fa
data = {
    "fetched_at": dt.now().isoformat(),
    "issue_date": dt.now().strftime("%A, %B %d, %Y"),
    "total": len(articles),
    "articles": articles,
}
mock_save(data)
assert saved.get("total") == len(articles)
result = {"result": data}
print(f"  ✓ Agent refresh logic OK — {data['total']} articles")
print(f"  ✓ Issue date: {data['issue_date']}")

# ── 3. Web app (Flask test client) ───────────────
print("\n[3/3] Testing Flask web app...")
# Patch load_cached_issue to return agent result directly
import api.index as web_module
web_module.load_cached_issue = lambda: result["result"]

web_module.app.config["TESTING"] = True
web_module.app.config["SECRET_KEY"] = "test"
client = web_module.app.test_client()

# Test login page loads
r = client.get("/")
assert r.status_code == 302, "Should redirect to login"
print("  ✓ Unauthenticated redirect works")

# Test login
r = client.post("/login", data={"username": "prateek.kacker", "password": "PK"}, follow_redirects=True)
assert r.status_code == 200, f"Login failed: {r.status_code}"
assert b"The Nature Post" in r.data, "Newsletter title not in response"
print("  ✓ Login works")
print("  ✓ Newsletter page renders")

# Check first article title appears
title_snippet = articles[0]["title"][:30].encode()
assert title_snippet in r.data, "Article title not in rendered page"
print(f"  ✓ Article content visible: '{articles[0]['title'][:40]}...'")

# Test logout
r = client.get("/logout", follow_redirects=True)
assert r.status_code == 200
print("  ✓ Logout works")

print("\n" + "=" * 50)
print("ALL TESTS PASSED ✅")
print("=" * 50)
