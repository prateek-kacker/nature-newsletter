import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
}

CATEGORIES = [
    {"label": "News", "url": "https://www.nature.com/nature/articles?type=news-&year=2026", "topic": "News"},
    {"label": "Research", "url": "https://www.nature.com/nature/research-articles?year=2026", "topic": "Research"},
    {"label": "News & Views", "url": "https://www.nature.com/nature/articles?type=news-and-views-&year=2026", "topic": "News & Views"},
]

def fetch_articles(max_per_category=4):
    articles = []
    for cat in CATEGORIES:
        try:
            resp = requests.get(cat["url"], headers=HEADERS, timeout=15)
            soup = BeautifulSoup(resp.text, "html.parser")
            for item in soup.select("article")[:max_per_category]:
                title_el = item.select_one("h3 a, h2 a")
                summary_el = item.select_one("p")
                if not title_el:
                    continue
                href = title_el.get("href", "")
                articles.append({
                    "topic": cat["topic"],
                    "title": title_el.get_text(strip=True),
                    "link": f"https://www.nature.com{href}" if href.startswith("/") else href,
                    "simple_summary": summary_el.get_text(strip=True) if summary_el else "",
                    "why_it_matters": "",
                    "read_time_minutes": 4,
                })
        except Exception as e:
            print(f"Error fetching {cat['label']}: {e}")
    return articles
