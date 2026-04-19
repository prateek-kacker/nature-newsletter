from bedrock_agentcore.runtime import BedrockAgentCoreApp
from datetime import datetime
from fetcher import fetch_articles

app = BedrockAgentCoreApp()

@app.entrypoint
def invoke(payload):
    """
    Nature Weekly Newsletter Agent.
    Accepts a payload with an optional 'action' key:
      - 'fetch'   : returns latest articles from Nature (default)
      - 'summary' : returns a plain-text digest
    """
    action = payload.get("action", "fetch")
    articles = fetch_articles()

    if action == "summary":
        lines = [f"Nature Weekly — {datetime.now().strftime('%B %d, %Y')}", ""]
        for a in articles:
            lines.append(f"[{a['topic']}] {a['title']}")
            if a["summary"]:
                lines.append(f"  {a['summary']}")
            lines.append(f"  {a['link']}")
            lines.append("")
        return {"result": "\n".join(lines)}

    # Default: return structured JSON
    return {
        "result": {
            "fetched_at": datetime.now().isoformat(),
            "total": len(articles),
            "articles": articles,
        }
    }

if __name__ == "__main__":
    app.run()
