"""
agent.py — Amazon Bedrock AgentCore entrypoint.

Runs weekly (triggered by EventBridge every Thursday).
Fetches Nature RSS, rewrites with Claude AI, saves to S3 cache.
The web app reads from S3 — no live fetching on user requests.
"""
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from datetime import datetime
from fetcher import fetch_articles
import boto3
import json
import os

app = BedrockAgentCoreApp()

S3_BUCKET = os.environ.get("CACHE_BUCKET", "nature-weekly-cache")
S3_KEY = "latest.json"


def save_to_s3(data: dict):
    """Persist the weekly issue to S3 so the web app can read it."""
    s3 = boto3.client("s3")
    s3.put_object(
        Bucket=S3_BUCKET,
        Key=S3_KEY,
        Body=json.dumps(data),
        ContentType="application/json",
    )
    print(f"Saved {len(data['articles'])} articles to s3://{S3_BUCKET}/{S3_KEY}")


def load_from_s3() -> dict | None:
    """Load the latest cached issue from S3."""
    try:
        s3 = boto3.client("s3")
        obj = s3.get_object(Bucket=S3_BUCKET, Key=S3_KEY)
        return json.loads(obj["Body"].read())
    except Exception as e:
        print(f"Cache miss or S3 error: {e}")
        return None


@app.entrypoint
def invoke(payload: dict) -> dict:
    """
    AgentCore entrypoint.

    Actions:
      refresh (default) — fetch + summarize + save to S3
      read              — return cached issue from S3
      summary           — return plain-text digest from cache
    """
    action = payload.get("action", "refresh")

    if action == "read":
        cached = load_from_s3()
        if cached:
            return {"result": cached}
        return {"result": {"error": "No cached issue found. Run refresh first."}}

    if action == "summary":
        cached = load_from_s3()
        if not cached:
            return {"result": "No cached issue. Run refresh first."}
        lines = [f"Nature Weekly — {cached.get('fetched_at', '')}", ""]
        for a in cached.get("articles", []):
            lines.append(f"[{a['topic']}] {a['title']}")
            lines.append(f"  {a.get('simple_summary', '')}")
            lines.append(f"  {a['link']}")
            lines.append("")
        return {"result": "\n".join(lines)}

    # Default: refresh — fetch, summarize, cache
    articles = fetch_articles()
    data = {
        "fetched_at": datetime.now().isoformat(),
        "issue_date": datetime.now().strftime("%A, %B %d, %Y"),
        "total": len(articles),
        "articles": articles,
    }
    save_to_s3(data)
    return {"result": data}


if __name__ == "__main__":
    app.run()
