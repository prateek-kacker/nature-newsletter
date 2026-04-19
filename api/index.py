from flask import Flask, render_template_string
import requests
from bs4 import BeautifulSoup
from datetime import datetime

app = Flask(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
}

CATEGORIES = [
    {"label": "News", "url": "https://www.nature.com/nature/articles?type=news-&year=2026", "icon": "📰", "color": "#e63946", "dark_color": "#ff6b6b"},
    {"label": "Research", "url": "https://www.nature.com/nature/research-articles?year=2026", "icon": "🔬", "color": "#2a9d8f", "dark_color": "#00f5d4"},
    {"label": "News & Views", "url": "https://www.nature.com/nature/articles?type=news-and-views-&year=2026", "icon": "💡", "color": "#b5830a", "dark_color": "#ffe66d"},
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
<html lang="en" data-theme="broadsheet">
<head>
    <meta charset="UTF-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
    <title>Nature Weekly — {{ date_str }}</title>
    <style>
        /* ── Base reset ── */
        * { box-sizing: border-box; margin: 0; padding: 0; }

        /* ══════════════════════════════════════
           THEME 1: BROADSHEET (Classic Newspaper)
        ══════════════════════════════════════ */
        [data-theme="broadsheet"] {
            --bg: #f5f0e8;
            --surface: #fffef9;
            --text: #111;
            --subtext: #444;
            --border: #222;
            --header-bg: #111;
            --header-text: #f5f0e8;
            --accent: #111;
            --link: #111;
            --link-hover: #555;
            --more: #555;
            --divider: #222;
            --badge-bg: #111;
            --badge-text: #f5f0e8;
            --toggle-bg: #111;
            --toggle-text: #f5f0e8;
            --shadow: none;
            --card-border: 1px solid #bbb;
            --radius: 0;
            --font-body: 'Georgia', 'Times New Roman', serif;
            --font-ui: 'Georgia', serif;
        }

        /* ══════════════════════════════════════
           THEME 2: DARK MODE (Science Journal)
        ══════════════════════════════════════ */
        [data-theme="dark"] {
            --bg: #0a0e1a;
            --surface: #111827;
            --text: #e2e8f0;
            --subtext: #94a3b8;
            --border: #1e293b;
            --header-bg: #060912;
            --header-text: #e2e8f0;
            --accent: #00f5d4;
            --link: #e2e8f0;
            --link-hover: #00f5d4;
            --more: #00f5d4;
            --divider: #1e293b;
            --badge-bg: #00f5d4;
            --badge-text: #0a0e1a;
            --toggle-bg: #00f5d4;
            --toggle-text: #0a0e1a;
            --shadow: 0 0 20px rgba(0, 245, 212, 0.08);
            --card-border: 1px solid #1e293b;
            --radius: 10px;
            --font-body: 'Inter', 'Segoe UI', sans-serif;
            --font-ui: 'Inter', 'Segoe UI', sans-serif;
        }

        /* ── Layout ── */
        body {
            font-family: var(--font-body);
            background: var(--bg);
            color: var(--text);
            line-height: 1.75;
            transition: background 0.3s, color 0.3s;
        }

        /* ── Theme toggle ── */
        .theme-toggle {
            position: fixed;
            top: 18px;
            right: 20px;
            z-index: 100;
            background: var(--toggle-bg);
            color: var(--toggle-text);
            border: none;
            padding: 8px 16px;
            font-size: 0.8rem;
            font-family: var(--font-ui);
            font-weight: 700;
            cursor: pointer;
            border-radius: var(--radius);
            letter-spacing: 1px;
            text-transform: uppercase;
            transition: all 0.3s;
        }
        .theme-toggle:hover { opacity: 0.85; }

        /* ── Header ── */
        header {
            background: var(--header-bg);
            color: var(--header-text);
            padding: 60px 20px 40px;
            text-align: center;
            border-bottom: 4px double var(--divider);
            position: relative;
        }

        [data-theme="broadsheet"] header {
            border-bottom: 4px double #555;
        }

        [data-theme="broadsheet"] .masthead-rule {
            border: none;
            border-top: 1px solid #555;
            margin: 12px auto;
            width: 60%;
        }

        [data-theme="dark"] .masthead-rule {
            border: none;
            border-top: 1px solid #00f5d4;
            margin: 12px auto;
            width: 60%;
            box-shadow: 0 0 8px rgba(0,245,212,0.4);
        }

        header h1 {
            font-family: var(--font-body);
            font-size: 3rem;
            letter-spacing: 4px;
            text-transform: uppercase;
            margin-bottom: 6px;
        }

        [data-theme="dark"] header h1 {
            color: #00f5d4;
            text-shadow: 0 0 20px rgba(0,245,212,0.5);
            letter-spacing: 6px;
        }

        header p {
            font-size: 0.95rem;
            opacity: 0.7;
            font-style: italic;
            margin-bottom: 14px;
        }

        [data-theme="dark"] header p { font-style: normal; }

        .badge {
            display: inline-block;
            background: var(--badge-bg);
            color: var(--badge-text);
            font-size: 0.75rem;
            padding: 4px 14px;
            font-family: var(--font-ui);
            letter-spacing: 1px;
            text-transform: uppercase;
            border-radius: var(--radius);
        }

        [data-theme="dark"] .badge {
            box-shadow: 0 0 10px rgba(0,245,212,0.3);
        }

        /* ── Main ── */
        main { max-width: 1060px; margin: 50px auto; padding: 0 24px; }

        /* ── Section ── */
        .section { margin-bottom: 60px; }

        .section-header {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 24px;
        }

        [data-theme="broadsheet"] .section-header {
            border-bottom: 3px solid #111;
            padding-bottom: 8px;
        }

        [data-theme="dark"] .section-header {
            border-bottom: 1px solid var(--divider);
            padding-bottom: 10px;
        }

        .section-title {
            font-size: 1.3rem;
            font-family: var(--font-body);
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 2px;
        }

        [data-theme="dark"] .section-title { color: var(--accent); }

        .section-icon { font-size: 1.2rem; }

        /* ── Cards grid ── */
        [data-theme="broadsheet"] .grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 0;
            border-top: 1px solid #bbb;
            border-left: 1px solid #bbb;
        }

        [data-theme="dark"] .grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 18px;
        }

        /* ── Cards ── */
        [data-theme="broadsheet"] .card {
            background: var(--surface);
            padding: 22px;
            border-right: 1px solid #bbb;
            border-bottom: 1px solid #bbb;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        [data-theme="dark"] .card {
            background: var(--surface);
            border: var(--card-border);
            border-radius: var(--radius);
            padding: 22px;
            display: flex;
            flex-direction: column;
            gap: 10px;
            box-shadow: var(--shadow);
            transition: transform 0.2s, box-shadow 0.2s, border-color 0.2s;
        }

        [data-theme="dark"] .card:hover {
            transform: translateY(-4px);
            border-color: #00f5d4;
            box-shadow: 0 0 24px rgba(0,245,212,0.15);
        }

        [data-theme="broadsheet"] .card:hover { background: #fffde7; }

        .card a.title {
            font-size: 1rem;
            font-weight: bold;
            color: var(--link);
            text-decoration: none;
            font-family: var(--font-body);
            line-height: 1.4;
        }

        [data-theme="broadsheet"] .card a.title { font-size: 1.05rem; }

        .card a.title:hover { color: var(--link-hover); text-decoration: underline; }

        .card p {
            font-size: 0.87rem;
            color: var(--subtext);
            flex-grow: 1;
            font-family: var(--font-body);
        }

        .card a.more {
            font-size: 0.8rem;
            color: var(--more);
            font-family: var(--font-ui);
            font-weight: 700;
            text-decoration: none;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        [data-theme="broadsheet"] .card a.more::after { content: " ›"; }
        [data-theme="dark"] .card a.more::after { content: " →"; }

        .card a.more:hover { text-decoration: underline; }

        /* ── Footer ── */
        footer {
            text-align: center;
            padding: 30px;
            font-size: 0.8rem;
            color: var(--subtext);
            font-family: var(--font-ui);
            border-top: 2px solid var(--divider);
            margin-top: 20px;
        }

        [data-theme="broadsheet"] footer { border-top: 3px double #555; }

        footer a { color: var(--more); }

        /* ── Dark scanline overlay ── */
        [data-theme="dark"] body::before {
            content: "";
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: repeating-linear-gradient(
                0deg,
                transparent,
                transparent 2px,
                rgba(0,0,0,0.03) 2px,
                rgba(0,0,0,0.03) 4px
            );
            pointer-events: none;
            z-index: 0;
        }

        main, header, footer { position: relative; z-index: 1; }
    </style>
</head>
<body>
<button class="theme-toggle" onclick="toggleTheme()" id="toggle-btn">☀ Broadsheet</button>

<header>
    <hr class="masthead-rule"/>
    <h1>🌿 Nature Weekly</h1>
    <p>Your simplified digest of the latest science from Nature magazine</p>
    <hr class="masthead-rule"/>
    <span class="badge">Week of {{ date_str }} &nbsp;·&nbsp; {{ total }} articles</span>
</header>

<main>
    {% for cat in categories %}
    <section class="section">
        <div class="section-header">
            <span class="section-icon">{{ cat.icon }}</span>
            <h2 class="section-title" data-light-color="{{ cat.color }}" data-dark-color="{{ cat.dark_color }}">
                {{ cat.label }}
            </h2>
        </div>
        <div class="grid">
            {% for a in cat.articles %}
            <div class="card">
                <a class="title" href="{{ a.link }}" target="_blank">{{ a.title }}</a>
                {% if a.summary %}<p>{{ a.summary }}</p>{% endif %}
                <a class="more" href="{{ a.link }}" target="_blank">Read full article</a>
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

<script>
    const html = document.documentElement;
    const btn = document.getElementById('toggle-btn');

    function applyTheme(theme) {
        html.setAttribute('data-theme', theme);
        btn.textContent = theme === 'dark' ? '🗞 Broadsheet' : '🌙 Dark Mode';
        localStorage.setItem('nw-theme', theme);
        updateSectionColors(theme);
    }

    function updateSectionColors(theme) {
        document.querySelectorAll('.section-title').forEach(el => {
            el.style.color = theme === 'dark'
                ? el.dataset.darkColor
                : el.dataset.lightColor;
        });
    }

    function toggleTheme() {
        const current = html.getAttribute('data-theme');
        applyTheme(current === 'dark' ? 'broadsheet' : 'dark');
    }

    // Load saved preference
    const saved = localStorage.getItem('nw-theme') || 'broadsheet';
    applyTheme(saved);
</script>
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
