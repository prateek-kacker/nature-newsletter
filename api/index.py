from flask import Flask, render_template_string, request, session, redirect, url_for
from datetime import datetime
import os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from agent import invoke

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "nature-weekly-secret")

VALID_USERNAME = "prateek.kacker"
VALID_PASSWORD = "PK"

def to_roman(num):
    romans = ["I","II","III","IV","V","VI","VII","VIII","IX","X","XI","XII","XIII","XIV","XV","XVI","XVII","XVIII","XIX","XX"]
    return romans[num - 1] if 1 <= num <= 20 else str(num)

LOGIN_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
    <title>The Nature Post — Sign In</title>
    <style>
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
        body { min-height: 100vh; display: flex; align-items: center; justify-content: center;
               background: #f5f1e8; font-family: Georgia, 'Times New Roman', serif; padding: 2rem 1rem; }
        .card { max-width: 420px; width: 100%; background: white; border: 1px solid #d6d3d1;
                padding: 3rem 2.5rem; box-shadow: 0 2px 20px rgba(0,0,0,0.06); }
        .eyebrow { display: flex; align-items: center; justify-content: center; gap: 10px;
                   color: #78716c; font-size: 10px; letter-spacing: 0.3em;
                   font-family: ui-sans-serif, system-ui, sans-serif; margin-bottom: 12px; }
        .eyebrow hr { width: 24px; border: none; border-top: 1px solid #a8a29e; }
        h1 { text-align: center; font-size: clamp(1.75rem, 5vw, 2.5rem); font-weight: 500;
             letter-spacing: -0.02em; line-height: 0.95; color: #1c1917; }
        .subtitle { text-align: center; font-style: italic; color: #78716c; font-size: 13px; margin-top: 8px; }
        .rule { border-top: 2px solid #1c1917; border-bottom: 1px solid #1c1917; padding: 8px 4px; margin: 28px 0; }
        .rule p { text-align: center; font-size: 10px; letter-spacing: 0.25em; color: #1c1917;
                  font-family: ui-sans-serif, system-ui, sans-serif; text-transform: uppercase; }
        label { display: block; font-size: 10px; letter-spacing: 0.25em; color: #57534e;
                font-family: ui-sans-serif, system-ui, sans-serif; text-transform: uppercase; margin-bottom: 8px; }
        .field { margin-bottom: 20px; }
        input { width: 100%; padding: 12px 16px; border: 1px solid #a8a29e; font-family: Georgia, serif;
                font-size: 15px; color: #1c1917; background: white; outline: none; transition: border-color 0.2s; }
        input:focus { border-color: #1c1917; }
        .error { display: flex; align-items: flex-start; gap: 8px; background: #fef2f2;
                 border: 1px solid #fecaca; padding: 10px 12px; margin-bottom: 20px; color: #7f1d1d; }
        .error p { font-style: italic; font-size: 13px; line-height: 1.5; }
        .btn { width: 100%; padding: 12px; background: #1c1917; color: white; border: none; cursor: pointer;
               font-family: ui-sans-serif, system-ui, sans-serif; font-size: 12px; letter-spacing: 0.2em;
               text-transform: uppercase; display: flex; align-items: center; justify-content: center;
               gap: 8px; transition: background 0.2s; }
        .btn:hover { background: #44403c; }
        .footer-note { text-align: center; color: #a8a29e; font-style: italic; font-size: 12px; margin-top: 32px; }
    </style>
</head>
<body>
<div class="card">
    <div class="eyebrow">
        <hr/> 🌿 <span>Subscribers only</span> 🌿 <hr/>
    </div>
    <h1>The Nature Post</h1>
    <p class="subtitle">Please sign in to read this week's issue.</p>
    <div class="rule">
        <p>Private edition · For Prateek</p>
    </div>
    <form method="POST" action="/login">
        <div class="field">
            <label>Username</label>
            <input type="text" name="username" autofocus autocomplete="username" spellcheck="false"/>
        </div>
        <div class="field">
            <label>Password</label>
            <input type="password" name="password" autocomplete="current-password"/>
        </div>
        {% if error %}
        <div class="error">
            <span>⚠</span>
            <p>{{ error }}</p>
        </div>
        {% endif %}
        <button type="submit" class="btn">🔒 Sign in</button>
    </form>
    <p class="footer-note">Exclusively for invited readers.</p>
</div>
</body>
</html>"""

MAIN_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
    <title>The Nature Post — {{ date_str }}</title>
    <style>
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
        body { min-height: 100vh; padding: 2rem 1rem; background: #f5f1e8;
               font-family: Georgia, 'Times New Roman', serif; }
        .paper { max-width: 896px; margin: 0 auto; background: white;
                 border: 1px solid #d6d3d1; box-shadow: 0 2px 20px rgba(0,0,0,0.06); }
        .inner { padding: 2.5rem 1.5rem; }
        @media(min-width:768px){ .inner { padding: 3rem 3.5rem; } }

        /* Header */
        .eyebrow { display: flex; align-items: center; justify-content: center; gap: 10px;
                   color: #78716c; font-size: 10px; letter-spacing: 0.3em;
                   font-family: ui-sans-serif, system-ui, sans-serif; margin-bottom: 12px; }
        .eyebrow hr { width: 32px; border: none; border-top: 1px solid #a8a29e; }
        h1.masthead { text-align: center; font-size: clamp(2.25rem, 7vw, 4.5rem);
                      font-weight: 500; letter-spacing: -0.02em; line-height: 0.95; color: #1c1917; }
        .tagline { text-align: center; font-style: italic; color: #78716c; font-size: 14px; margin-top: 12px; }
        .dateline { border-top: 3px solid #1c1917; border-bottom: 1px solid #1c1917;
                    padding: 8px 4px; margin-top: 24px; }
        .dateline-inner { display: flex; align-items: center; justify-content: space-between;
                          font-size: 11px; letter-spacing: 0.2em; color: #1c1917;
                          font-family: ui-sans-serif, system-ui, sans-serif; text-transform: uppercase; }

        /* Lead story */
        .lead { padding-bottom: 2.5rem; border-bottom: 1px solid #d6d3d1; margin-top: 2.5rem; }
        .topic-label { font-size: 11px; letter-spacing: 0.25em; color: #78716c;
                       font-family: ui-sans-serif, system-ui, sans-serif; text-transform: uppercase; margin-bottom: 16px; }
        .topic-label span { margin: 0 8px; }
        h2.lead-title { font-size: clamp(1.875rem, 5vw, 3rem); font-weight: 500; color: #1c1917;
                        letter-spacing: -0.015em; line-height: 1.05; margin-bottom: 20px; }
        .meta { display: flex; align-items: center; gap: 10px; font-size: 12px; color: #78716c;
                font-family: ui-sans-serif, system-ui, sans-serif; margin-bottom: 24px; flex-wrap: wrap; }
        .lead-body { font-size: 18px; line-height: 1.75; color: #292524; }
        .drop-cap { float: left; font-size: 68px; line-height: 0.85; margin-top: 6px;
                    margin-right: 8px; font-weight: 500; color: #1c1917; font-family: Georgia, serif; }
        .why-box { margin-top: 32px; padding-left: 20px; border-left: 2px solid #1c1917; }
        .why-label { font-size: 11px; letter-spacing: 0.25em; color: #78716c;
                     font-family: ui-sans-serif, system-ui, sans-serif; text-transform: uppercase; margin-bottom: 4px; }
        .why-text { font-style: italic; color: #44403c; font-size: 16px; line-height: 1.7; }
        .read-link { display: inline-flex; align-items: center; gap: 6px; margin-top: 28px;
                     font-size: 12px; letter-spacing: 0.15em; color: #1c1917; text-decoration: none;
                     border-bottom: 1.5px solid #1c1917; padding-bottom: 2px;
                     font-family: ui-sans-serif, system-ui, sans-serif; text-transform: uppercase; }
        .read-link:hover { opacity: 0.6; }

        /* Secondary grid */
        .grid { display: grid; }
        @media(min-width:768px){ .grid { grid-template-columns: 1fr 1fr; } }
        .grid-item { padding: 2rem 0; }
        .grid-item:not(:last-child) { border-bottom: 1px solid #d6d3d1; }
        @media(min-width:768px){
            .grid-item:nth-child(odd) { padding-right: 2rem; border-right: 1px solid #d6d3d1; border-bottom: none; }
            .grid-item:nth-child(even) { padding-left: 2rem; border-bottom: none; }
            .grid-row:not(:first-child) .grid-item { border-top: 1px solid #d6d3d1; }
        }
        h3.art-title { font-size: 22px; font-weight: 500; color: #1c1917; letter-spacing: -0.01em;
                       line-height: 1.2; margin-bottom: 12px; }
        .art-meta { font-size: 11px; color: #78716c; font-family: ui-sans-serif, system-ui, sans-serif;
                    margin-bottom: 16px; }
        .art-summary { font-size: 15px; line-height: 1.7; color: #44403c; margin-bottom: 16px; }
        .art-why { padding-left: 12px; border-left: 1px solid #a8a29e; margin-bottom: 20px; }
        .art-why-label { font-size: 10px; letter-spacing: 0.2em; color: #78716c;
                         font-family: ui-sans-serif, system-ui, sans-serif; text-transform: uppercase; }
        .art-why-text { font-style: italic; color: #57534e; font-size: 13px; line-height: 1.65; }

        /* Disclaimer */
        .disclaimer { background: #fafaf9; border: 1px solid #e7e5e4; border-left: 3px solid #a8a29e;
                      padding: 14px 18px; margin-top: 2.5rem; }
        .disclaimer p { font-size: 11px; line-height: 1.8; color: #78716c;
                        font-family: ui-sans-serif, system-ui, sans-serif; }
        .disclaimer a { color: #1c1917; }
        .ai-badge { display: inline-block; font-size: 9px; letter-spacing: 0.15em; text-transform: uppercase;
                    background: #e7e5e4; color: #78716c; padding: 2px 6px; border-radius: 2px;
                    font-family: ui-sans-serif, system-ui, sans-serif; vertical-align: middle; margin-left: 4px; }

        /* Footer */
        .paper-footer { border-top: 1px solid #1c1917; margin-top: 2rem; padding-top: 1.5rem;
                        display: flex; flex-direction: column; gap: 16px; }
        @media(min-width:640px){ .paper-footer { flex-direction: row; align-items: center; justify-content: space-between; } }
        .footer-note { font-size: 11px; line-height: 1.7; color: #78716c;
                       font-family: ui-sans-serif, system-ui, sans-serif; }
        .footer-actions { display: flex; align-items: center; gap: 20px; }
        .signout-btn { display: inline-flex; align-items: center; gap: 6px; font-size: 11px;
                       letter-spacing: 0.15em; color: #78716c; background: none; border: none;
                       cursor: pointer; font-family: ui-sans-serif, system-ui, sans-serif;
                       text-transform: uppercase; text-decoration: none; }
        .signout-btn:hover { color: #1c1917; }
        .refresh-btn { display: inline-flex; align-items: center; gap: 8px; padding: 10px 20px;
                       background: #1c1917; color: white; border: none; cursor: pointer;
                       font-family: ui-sans-serif, system-ui, sans-serif; font-size: 11px;
                       letter-spacing: 0.2em; text-transform: uppercase; text-decoration: none; }
        .refresh-btn:hover { background: #44403c; }
    </style>
</head>
<body>
<div class="paper">
  <div class="inner">

    <header>
      <div class="eyebrow">
        <hr/> 🌿 <span>A weekly science digest</span> 🌿 <hr/>
      </div>
      <h1 class="masthead">The Nature Post</h1>
      <p class="tagline">Science news, in plain words.</p>
      <div class="dateline">
        <div class="dateline-inner">
          <span>{{ date_str }}</span>
          <span class="hidden-sm">Weekly edition</span>
          <span>No. {{ issue_roman }}</span>
        </div>
      </div>
    </header>

    {% if lead %}
    <article class="lead">
      <p class="topic-label">
        <span>{{ lead.topic }}</span><span>—</span><span>Lead story</span>
      </p>
      <h2 class="lead-title">{{ lead.title }}</h2>
      <div class="meta">
        <span>⏱ {{ lead.read_time_minutes }} min read</span>
      </div>
      <p class="lead-body">
        <span class="drop-cap">{{ lead.simple_summary[0] }}</span>{{ lead.simple_summary[1:] }}
      </p>
      {% if lead.why_it_matters %}
      <div class="why-box">
        <p class="why-label">Why it matters</p>
        <p class="why-text">{{ lead.why_it_matters }}</p>
      </div>
      {% endif %}
      <a href="{{ lead.link }}" target="_blank" class="read-link">Read full article →</a>
    </article>

    {% for row in rows %}
    <div class="grid grid-row">
      {% for art in row %}
      <article class="grid-item">
        <p class="topic-label">{{ art.topic }}</p>
        <h3 class="art-title">{{ art.title }}</h3>
        <p class="art-meta">⏱ {{ art.read_time_minutes }} min read</p>
        <p class="art-summary">{{ art.simple_summary }}</p>
        {% if art.why_it_matters %}
        <div class="art-why">
          <span class="art-why-label">Why it matters — </span>
          <span class="art-why-text">{{ art.why_it_matters }}</span>
        </div>
        {% endif %}
        <a href="{{ art.link }}" target="_blank" class="read-link">Read full article →</a>
      </article>
      {% endfor %}
    </div>
    {% endfor %}
    {% endif %}

    <div class="disclaimer">
      <p>
        📋 <strong>Copyright notice:</strong>
        Article headlines and links are sourced from
        <a href="https://www.nature.com/nature.rss" target="_blank">Nature's official RSS feed</a>
        (© Springer Nature). All summaries on this page are
        <span class="ai-badge">AI rewritten</span>
        original plain-English interpretations — not reproductions of Nature's text.
        This is a personal, non-commercial digest. Read the full articles at
        <a href="https://www.nature.com" target="_blank">nature.com</a>.
      </p>
    </div>

    <footer class="paper-footer">
      <p class="footer-note">
        Headlines via <a href="https://www.nature.com/nature.rss" target="_blank">Nature RSS</a>
        · Summaries AI-generated · © Springer Nature for original articles
      </p>
      <div class="footer-actions">
        <a href="/logout" class="signout-btn">⬡ Sign out</a>
        <a href="/?refresh=1" class="refresh-btn">↻ Print next issue</a>
      </div>
    </footer>

  </div>
</div>
</body>
</html>"""

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        u = request.form.get("username", "").strip().lower()
        p = request.form.get("password", "")
        if u == VALID_USERNAME and p == VALID_PASSWORD:
            session["auth"] = True
            return redirect(url_for("index"))
        error = "Those credentials aren't on the subscribers list."
    return render_template_string(LOGIN_TEMPLATE, error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/")
def index():
    if not session.get("auth"):
        return redirect(url_for("login"))

    articles = invoke({"action": "fetch"}).get("result", {}).get("articles", [])
    lead = articles[0] if articles else None
    secondary = articles[1:]
    rows = [secondary[i:i+2] for i in range(0, len(secondary), 2)]

    date_str = datetime.now().strftime("%A, %B %d, %Y")
    issue_roman = to_roman(1)

    return render_template_string(
        MAIN_TEMPLATE,
        lead=lead,
        rows=rows,
        date_str=date_str,
        issue_roman=issue_roman
    )
