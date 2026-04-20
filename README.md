# 🌿 The Nature Post

A weekly science newsletter web app that fetches articles from Nature magazine's official RSS feed, rewrites them in plain English using Claude AI, and presents them in a classic newspaper-style layout.

## Architecture

```
fetcher.py        ← Fetches Nature RSS feed + rewrites summaries via Claude AI
    ↑
agent.py          ← Amazon Bedrock AgentCore entrypoint (AWS deployment)
    ↑
api/index.py      ← Flask web app (login, newspaper UI, routes)
```

## Features

- **Login-gated** — private edition for invited readers
- **Newspaper design** — broadsheet layout with lead story, drop cap, two-column grid
- **AI summaries** — Claude rewrites each article in plain English (no jargon)
- **Official RSS** — sourced from `nature.com/nature.rss` (not scraping)
- **Copyright safe** — AI-generated original summaries + clear attribution disclaimer
- **Weekly automation** — Windows Task Scheduler runs every Thursday at 9AM

## Setup

### 1. Install dependencies

```bash
pip install flask requests beautifulsoup4 bedrock-agentcore
```

### 2. Set environment variables

```bash
# Required for AI summaries
export ANTHROPIC_API_KEY=your_key_here

# Optional (defaults to a dev secret)
export SECRET_KEY=your_flask_secret
```

### 3. Run locally

```bash
python -m flask --app api/index.py run --port 5000
```

Visit `http://localhost:5000` and sign in with:
- Username: `prateek.kacker`
- Password: `PK`

## Deploy to Vercel

1. Push to GitHub
2. Import repo at [vercel.com/new](https://vercel.com/new)
3. Add environment variables in Vercel dashboard:
   - `ANTHROPIC_API_KEY`
   - `SECRET_KEY`
4. Deploy

## Deploy to AWS AgentCore

Requires AWS CLI, Docker, and `uv` installed.

```bash
# Configure the agent
agentcore configure --entrypoint agent.py \
  --execution-role arn:aws:iam::YOUR_ACCOUNT:role/NatureWeeklyAgentCoreRole \
  --name natureweekly --non-interactive \
  --deployment-type direct_code_deploy --runtime PYTHON_3_13

# Deploy
agentcore deploy

# Test
agentcore invoke '{"action": "fetch"}'
agentcore invoke '{"action": "summary"}'
```

> Note: AgentCore requires the service to be enabled on your AWS account.
> Request access via AWS Support if `Total Agents` quota shows 0.

## Weekly Automation (Windows)

A Windows Task Scheduler task runs every Thursday at 9AM:
- Task name: `Nature Weekly Newsletter`
- Runs: `python run_weekly.py`
- Generates a local `newsletter.html` and opens it in your browser

## Copyright

Article headlines sourced from [Nature's official RSS feed](https://www.nature.com/nature.rss) (© Springer Nature).
All summaries are AI-generated original plain-English interpretations — not reproductions of Nature's text.
This is a personal, non-commercial digest.
