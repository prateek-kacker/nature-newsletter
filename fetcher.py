"""
fetcher.py — Fetches articles from Nature's official RSS feed
and rewrites them in plain English using Claude AI.
"""
import requests
import xml.etree.ElementTree as ET
import os
import re

RSS_FEEDS = [
    {"url": "https://www.nature.com/nature.rss", "topic": "Nature"},
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
}

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")


def fetch_from_rss(max_articles=6):
    """Fetch article titles and links from Nature's official RSS feed."""
    articles = []
    # Nature uses RSS 1.0 (RDF) with namespaces
    NS = {
        "rss": "http://purl.org/rss/1.0/",
        "dc":  "http://purl.org/dc/elements/1.1/",
        "content": "http://purl.org/rss/1.0/modules/content/",
    }
    for feed in RSS_FEEDS:
        try:
            resp = requests.get(feed["url"], headers=HEADERS, timeout=15)
            root = ET.fromstring(resp.content)
            items = root.findall("rss:item", NS)[:max_articles]
            for item in items:
                title = (item.findtext("rss:title", "", NS) or
                         item.findtext("dc:title", "", NS)).strip()
                link  = (item.findtext("rss:link", "", NS)).strip()
                # content:encoded has the description, strip HTML
                raw   = (item.findtext("content:encoded", "", NS) or
                         item.findtext("rss:description", "", NS) or "")
                description = re.sub(r"<[^>]+>", "", raw).strip()[:300]
                if not title or not link:
                    continue
                articles.append({
                    "topic": feed["topic"],
                    "title": title,
                    "link": link,
                    "original_summary": description,
                })
        except Exception as e:
            print(f"Error fetching RSS {feed['url']}: {e}")
    return articles


def rewrite_with_ai(articles):
    """
    Use Claude to rewrite article summaries in plain English.
    Falls back to original title + link if API key not set.
    """
    if not ANTHROPIC_API_KEY:
        # No API key — return articles with original summaries, clearly marked
        for a in articles:
            a["simple_summary"] = a.get("original_summary", "")
            a["why_it_matters"] = ""
            a["read_time_minutes"] = 4
            a["ai_rewritten"] = False
        return articles

    rewritten = []
    for article in articles:
        try:
            prompt = f"""Rewrite this Nature magazine article in plain, simple English for a curious reader with NO science background.

Article title: {article['title']}
Brief description: {article.get('original_summary', '')}

Write:
1. simple_summary: 2-3 sentences explaining the science without jargon, using everyday words and analogies
2. why_it_matters: 1 sentence on real-world significance

Respond ONLY as JSON:
{{"simple_summary": "...", "why_it_matters": "..."}}"""

            resp = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-haiku-4-5",
                    "max_tokens": 300,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=20,
            )
            data = resp.json()
            if "content" not in data or not data["content"]:
                raise ValueError(f"Unexpected API response: {data}")
            text = data["content"][0]["text"].strip()
            # Parse JSON response
            import json
            parsed = json.loads(text[text.index("{"):text.rindex("}") + 1])
            article["simple_summary"] = parsed.get("simple_summary", "")
            article["why_it_matters"] = parsed.get("why_it_matters", "")
            article["ai_rewritten"] = True
        except Exception as e:
            print(f"AI rewrite failed for '{article['title']}': {e}")
            article["simple_summary"] = article.get("original_summary", "")
            article["why_it_matters"] = ""
            article["ai_rewritten"] = False

        article["read_time_minutes"] = 4
        rewritten.append(article)

    return rewritten


def fetch_articles():
    """Main entry point: fetch from RSS + rewrite with AI."""
    articles = fetch_from_rss()
    return rewrite_with_ai(articles)

if __name__ == "__main__":
    arts = fetch_articles()
    print(f"Got {len(arts)} articles\n")
    for a in arts[:3]:
        print("TITLE:", a["title"])
        print("SUMMARY:", a["simple_summary"])
        print("WHY:", a["why_it_matters"])
        print("AI rewritten:", a["ai_rewritten"])
        print()
