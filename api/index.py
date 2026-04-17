from flask import Flask, render_template_string
import requests
from bs4 import BeautifulSoup
from datetime import datetime

app = Flask(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
}

CATEGORIES = [
    {"label": "News", "url": "https://www.nature.com/nature/articles?type=news-&year=2026", "icon": "📰", "color": "#e63946"},
    {"label": "Research", "url": "https://www.nature.com/nature/research-articles?year=2026", "icon": "🔬", "color": "#2a9d8f"},
    {"label": "News & Views", "url": "https://www.nature.com/nature/articles?type=news-and-views-&year=2026", "icon": "💡", "color": "#e9c46a"},
]

def fetch_articles(url, label, max_articles=6):
    articles = []
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        items = soup.select("article")[:max_articles]
        for item in items:
            title_el = item.select_one("h3 a, h2 a")
            summary_el = item.select_one("p")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            href = title_el.get("href", "")
            link = f"https://www.nature.com{href}" if href.startswith("/") else href
            summary = summary_el.get_text(strip=True) if summary_el else ""
            articles.append({"title": title, "link": link, "summary": summary})
    except Exception as e:
        print(f"Error fetching {label}: {e}")
    return articles

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
    <title>Nature Weekly — {{ date_str }}</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: Georgia, serif; background: #f4f1eb; color: #1a1a2e; line-height: 1.7; }
        header { background: #1a1a2e; color: white; padding: 50px 20px; text-align: center; }
        header h1 { font-size: 2.6rem; letter-spacing: 2px; margin-bottom: 8px; }
        header p { font-size: 1rem; color: #a8dadc; margin-bottom: 14px; }
        .badge { display: inline-block; background: #e63946; color: white; font-size: 0.78rem;
                 padding: 4px 14px; border-radius: 20px; font-family: sans-serif; }
        main { max-width: 1000px; margin: 50px auto; padding: 0 20px; }
        .section { margin-bottom: 55px; }
        .section-title { font-size: 1.4rem; font-family: sans-serif; font-weight: 700;
                         padding-left: 14px; margin-bottom: 22px; border-left: 5px solid {{ "var(--c)" }}; }
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px; }
        .card { background: white; border-radius: 12px; padding: 22px; box-shadow: 0 2px 8px rgba(0,0,0,0.07);
                display: flex; flex-direction: column; gap: 10px; transition: transform 0.2s, box-shadow 0.2s; }
        .card:hover { transform: translateY(-4px); box-shadow: 0 8px 20px rgba(0,0,0,0.12); }
        .card a.title { font-size: 1rem; font-weight: bold; color: #1a1a2e; text-decoration: none; }
        .card a.title:hover { color: #e63946; }
        .card p { font-size: 0.87rem; color: #555; flex-grow: 1; }
        .card a.more { font-size: 0.82rem; color: #2a9d8f; font-family: sans-serif; font-weight: 600; text-decoration: none; }
        .card a.more:hover { text-decoration: underline; }
        footer { text-align: center; padding: 30px; font-size: 0.8rem; color: #888;
                 font-family: sans-serif; border-top: 1px solid #ddd; margin-top: 20px; }
        footer a { color: #2a9d8f; }
    </style>
</head>
<body>
<header>
    <h1>🌿 Nature Weekly</h1>
    <p>Your simplified digest of the latest science from Nature magazine</p>
    <span class="badge">Week of {{ date_str }} &nbsp;·&nbsp; {{ total }} articles</span>
</header>
<main>
    {% for cat in categories %}
    <section class="section">
        <h2 class="section-title" style="border-left-color: {{ cat.color }};">
            {{ cat.icon }} {{ cat.label }}
        </h2>
        <div class="grid">
            {% for a in cat.articles %}
            <div class="card">
                <a class="title" href="{{ a.link }}" target="_blank">{{ a.title }}</a>
                {% if a.summary %}<p>{{ a.summary }}</p>{% endif %}
                <a class="more" href="{{ a.link }}" target="_blank">Read full article →</a>
            </div>
            {% endfor %}
        </div>
    </section>
    {% endfor %}
</main>
<footer>
    Content sourced from <a href="https://www.nature.com" target="_blank">nature.com</a>
    &nbsp;·&nbsp; Generated on {{ date_str }}
</footer>
</body>
</html>"""

@app.route("/")
def index():
    categories = []
    total = 0
    for cat in CATEGORIES:
        articles = fetch_articles(cat["url"], cat["label"])
        total += len(articles)
        categories.append({**cat, "articles": articles})

    date_str = datetime.now().strftime("%B %d, %Y")
    return render_template_string(HTML_TEMPLATE, categories=categories, date_str=date_str, total=total)
