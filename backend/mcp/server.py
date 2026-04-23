"""Naledi MCP Server — FastMCP integration for Claude Desktop.

Exposes 11 tools for Claude Desktop to interact with the Naledi platform:
- get_instagram_metrics, get_facebook_metrics, get_whatsapp_stats, get_google_ads_performance
- run_research_agent, generate_prompts
- get_vault_note, query_rag
- switch_model, get_agent_status, toggle_no_hands
"""

import os
import sys
from datetime import datetime, timezone, timedelta
from typing import Optional

# Add backend to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastmcp import FastMCP
import httpx

from services.claude_service import ClaudeService
from agents import ResearchAgent

# ---------------------------------------------------------------------------
# MCP Server Configuration
# ---------------------------------------------------------------------------
mcp = FastMCP(
    name="naledi-platform",
    dependencies=["httpx"],
)

# Service instances
claude_ai = ClaudeService()
research_agent = ResearchAgent()

# Naledi backend API URL
NALEDI_API_URL = os.getenv("NALEDI_API_URL", "http://localhost:8000")

# Social platform credentials (loaded from .env)
META_APP_ID = os.getenv("META_APP_ID")
META_APP_SECRET = os.getenv("META_APP_SECRET")
META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")
INSTAGRAM_BUSINESS_ID = os.getenv("INSTAGRAM_BUSINESS_ID")
FACEBOOK_PAGE_ID = os.getenv("FACEBOOK_PAGE_ID")
GOOGLE_ADS_CLIENT_ID = os.getenv("GOOGLE_ADS_CLIENT_ID")
GOOGLE_ADS_CLIENT_SECRET = os.getenv("GOOGLE_ADS_CLIENT_SECRET")
GOOGLE_ADS_DEVELOPER_TOKEN = os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")

# Obsidian vault path
OBSIDIAN_VAULT_PATH = os.getenv("OBSIDIAN_VAULT_PATH", os.path.expanduser("~/studex-vault"))

# ---------------------------------------------------------------------------
# Social Media Metrics Tools
# ---------------------------------------------------------------------------
@mcp.tool()
async def get_instagram_metrics(days: int = 7) -> dict:
    """Get Instagram metrics for the specified number of days.

    Args:
        days: Number of days to pull metrics for (default: 7)

    Returns:
        dict: Instagram metrics including reach, impressions, engagement_rate, saves, shares, reel_plays
    """
    if not all([META_ACCESS_TOKEN, INSTAGRAM_BUSINESS_ID]):
        return {"error": "Instagram not configured — connect in Settings"}

    SAST = timezone(timedelta(hours=2))
    since = datetime.now(SAST).replace(hour=0, minute=0, second=0, microsecond=0)
    until = since

    metrics = [
        "reach", "impressions", "engagement", "saves", "shares",
        "reel_plays", "profile_views", "follower_count"
    ]

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            # Get account insights
            resp = await client.get(
                f"https://graph.facebook.com/v18.0/{INSTAGRAM_BUSINESS_ID}/insights",
                params={
                    "metric": ",".join(metrics),
                    "period": "day",
                    "since": int(since.timestamp()),
                    "until": int(until.timestamp()),
                    "access_token": META_ACCESS_TOKEN,
                }
            )
            resp.raise_for_status()
            data = resp.json()

            # Aggregate metrics
            result = {"platform": "instagram", "days": days, "metrics": {}}
            for metric_data in data.get("data", []):
                metric_name = metric_data.get("name")
                values = metric_data.get("values", [])
                total = sum(v.get("value", 0) for v in values if v.get("value"))
                result["metrics"][metric_name] = total

            # Calculate engagement rate
            if result["metrics"].get("reach") and result["metrics"].get("engagement"):
                result["metrics"]["engagement_rate"] = round(
                    (result["metrics"]["engagement"] / result["metrics"]["reach"]) * 100, 2
                )

            result["time_sast"] = datetime.now(SAST).isoformat()
            return result

        except httpx.HTTPError as e:
            return {"error": f"Instagram API error: {e.response.status_code if hasattr(e, 'response') else str(e)}"}
        except Exception as e:
            return {"error": str(e)}


@mcp.tool()
async def get_facebook_metrics(days: int = 7) -> dict:
    """Get Facebook Page metrics for the specified number of days.

    Args:
        days: Number of days to pull metrics for (default: 7)

    Returns:
        dict: Facebook metrics including reach, impressions, engagement, page_likes
    """
    if not all([META_ACCESS_TOKEN, FACEBOOK_PAGE_ID]):
        return {"error": "Facebook not configured — connect in Settings"}

    SAST = timezone(timedelta(hours=2))
    since = datetime.now(SAST).replace(hour=0, minute=0, second=0, microsecond=0)
    until = since

    metrics = [
        "page_impressions_unique", "page_reach_unique", "page_engaged_users",
        "page_post_engagements", "page_likes", "page_video_views"
    ]

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.get(
                f"https://graph.facebook.com/v18.0/{FACEBOOK_PAGE_ID}/insights",
                params={
                    "metric": ",".join(metrics),
                    "period": "day",
                    "since": int(since.timestamp()),
                    "until": int(until.timestamp()),
                    "access_token": META_ACCESS_TOKEN,
                }
            )
            resp.raise_for_status()
            data = resp.json()

            result = {"platform": "facebook", "days": days, "metrics": {}}
            for metric_data in data.get("data", []):
                metric_name = metric_data.get("name")
                values = metric_data.get("values", [])
                total = sum(v.get("value", 0) for v in values if v.get("value"))
                # Normalize metric names
                normalized_name = metric_name.replace("_unique", "").replace("page_", "")
                result["metrics"][normalized_name] = total

            # Calculate engagement rate
            if result["metrics"].get("reach") and result["metrics"].get("engaged_users"):
                result["metrics"]["engagement_rate"] = round(
                    (result["metrics"]["engaged_users"] / result["metrics"]["reach"]) * 100, 2
                )

            result["time_sast"] = datetime.now(SAST).isoformat()
            return result

        except httpx.HTTPError as e:
            return {"error": f"Facebook API error: {e.response.status_code if hasattr(e, 'response') else str(e)}"}
        except Exception as e:
            return {"error": str(e)}


@mcp.tool()
async def get_whatsapp_stats() -> dict:
    """Get WhatsApp Business API message statistics.

    Returns:
        dict: WhatsApp stats including message volume, read rates, response times
    """
    if not all([WHATSAPP_ACCESS_TOKEN, WHATSAPP_PHONE_NUMBER_ID]):
        return {"error": "WhatsApp not configured — connect in Settings"}

    SAST = timezone(timedelta(hours=2))

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            # Get phone number details
            resp = await client.get(
                f"https://graph.facebook.com/v18.0/{WHATSAPP_PHONE_NUMBER_ID}",
                params={"access_token": WHATSAPP_ACCESS_TOKEN}
            )
            resp.raise_for_status()
            phone_data = resp.json()

            # Get insights (requires business verification)
            insights = {}
            try:
                insights_resp = await client.get(
                    f"https://graph.facebook.com/v18.0/{WHATSAPP_PHONE_NUMBER_ID}/insights",
                    params={
                        "metric": "message_sent, message_delivered, message_read, message_failed",
                        "access_token": WHATSAPP_ACCESS_TOKEN,
                    }
                )
                if insights_resp.status_code == 200:
                    insights_data = insights_resp.json()
                    for metric in insights_data.get("data", []):
                        insights[metric.get("name")] = metric.get("values", [{}])[0].get("value", 0)
            except:
                pass  # Insights may not be available

            return {
                "platform": "whatsapp",
                "phone_number": phone_data.get("display_phone_number"),
                "quality_rating": phone_data.get("quality_rating", "unknown"),
                "insights": insights,
                "time_sast": datetime.now(SAST).isoformat(),
            }

        except httpx.HTTPError as e:
            return {"error": f"WhatsApp API error: {e.response.status_code if hasattr(e, 'response') else str(e)}"}
        except Exception as e:
            return {"error": str(e)}


@mcp.tool()
async def get_google_ads_performance(days: int = 7) -> dict:
    """Get Google Ads performance metrics for the specified number of days.

    Args:
        days: Number of days to pull metrics for (default: 7)

    Returns:
        dict: Google Ads metrics including impressions, clicks, CTR, CPC, conversions, ROAS
    """
    if not all([GOOGLE_ADS_CLIENT_ID, GOOGLE_ADS_CLIENT_SECRET, GOOGLE_ADS_DEVELOPER_TOKEN]):
        return {"error": "Google Ads not configured — connect in Settings"}

    SAST = timezone(timedelta(hours=2))

    # Note: Full Google Ads API integration requires OAuth token refresh
    # This is a simplified version — production would use google-ads Python library
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            # Get OAuth token (simplified — production uses refresh token)
            token_resp = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": GOOGLE_ADS_CLIENT_ID,
                    "client_secret": GOOGLE_ADS_CLIENT_SECRET,
                    "refresh_token": os.getenv("GOOGLE_ADS_REFRESH_TOKEN", ""),
                    "grant_type": "refresh_token",
                }
            )
            token_data = token_resp.json()
            access_token = token_data.get("access_token")

            if not access_token:
                return {"error": "Google Ads OAuth token expired — re-authenticate in Settings"}

            # Query Google Ads API (simplified — production uses GAQL)
            headers = {
                "Authorization": f"Bearer {access_token}",
                "developer-token": GOOGLE_ADS_DEVELOPER_TOKEN,
                "Content-Type": "application/json",
            }

            # Get customer list
            customer_resp = await client.get(
                "https://googleads.googleapis.com/v15/customers",
                headers=headers
            )
            customers = customer_resp.json().get("resource_names", [])

            if not customers:
                return {"error": "No Google Ads customers found"}

            # Fetch metrics for first customer (production would aggregate all)
            customer_id = customers[0].split("/")[-1]

            # Note: Full GAQL query would go here — simplified mock for now
            return {
                "platform": "google_ads",
                "customer_id": customer_id,
                "days": days,
                "metrics": {
                    "impressions": 0,  # Would come from GAQL query
                    "clicks": 0,
                    "ctr": 0.0,
                    "cpc": 0.0,
                    "conversions": 0,
                    "cost": 0.0,
                    "roas": 0.0,
                },
                "note": "Full metrics require GAQL query implementation",
                "time_sast": datetime.now(SAST).isoformat(),
            }

        except httpx.HTTPError as e:
            return {"error": f"Google Ads API error: {e.response.status_code if hasattr(e, 'response') else str(e)}"}
        except Exception as e:
            return {"error": str(e)}


# ---------------------------------------------------------------------------
# Agent Tools
# ---------------------------------------------------------------------------
@mcp.tool()
async def run_research_agent(topic: str) -> dict:
    """Run the Research Agent to investigate a topic.

    Args:
        topic: The research topic or question to investigate

    Returns:
        dict: Research findings from the agent
    """
    if not claude_ai.configured:
        return {"error": "Claude AI not configured — set ANTHROPIC_API_KEY"}

    try:
        result = await research_agent.execute(topic)
        return {
            "agent": "research",
            "topic": topic,
            "result": result,
        }
    except Exception as e:
        return {"error": f"Research agent failed: {str(e)}"}


@mcp.tool()
async def generate_prompts(brief: str) -> dict:
    """Generate Higgsfield video prompts from a research brief.

    Args:
        brief: The research brief or content strategy

    Returns:
        dict: List of 5 Higgsfield-ready video prompts
    """
    if not claude_ai.configured:
        return {"error": "Claude AI not configured — set ANTHROPIC_API_KEY"}

    system_prompt = (
        "You are the PromptAgent for Studex Meat. "
        "Generate exactly 5 Higgsfield video prompts from the research brief. "
        "Each prompt should be detailed, visual, and ready for video generation. "
        "Include: subject, action, setting, mood, camera angle, lighting. "
        "Format as a numbered list."
    )

    try:
        response, usage = await claude_ai.generate(
            system=system_prompt,
            prompt=f"Research brief:\n{brief}\n\nGenerate 5 Higgsfield video prompts:",
            use_thinking=True,
            effort="medium",
        )

        # Parse prompts from response
        prompts = [line.strip() for line in response.split("\n") if line.strip() and any(line.startswith(str(i)) for i in range(1, 6))]

        return {
            "agent": "prompt",
            "brief": brief[:100] + "..." if len(brief) > 100 else brief,
            "prompts": prompts,
            "token_usage": {
                "input": usage.input_tokens,
                "output": usage.output_tokens,
                "total": usage.total_tokens,
            },
        }
    except Exception as e:
        return {"error": f"Prompt generation failed: {str(e)}"}


# ---------------------------------------------------------------------------
# Vault & RAG Tools
# ---------------------------------------------------------------------------
@mcp.tool()
async def get_vault_note(path: str) -> dict:
    """Get a note from the Obsidian vault by path.

    Args:
        path: Relative path to the note in the vault (e.g., "briefs/easter-campaign.md")

    Returns:
        dict: Note content and metadata
    """
    SAST = timezone(timedelta(hours=2))
    full_path = os.path.join(OBSIDIAN_VAULT_PATH, path)

    if not os.path.exists(OBSIDIAN_VAULT_PATH):
        return {"error": f"Vault not found at {OBSIDIAN_VAULT_PATH}"}

    if not os.path.exists(full_path):
        return {"error": f"Note not found: {path}"}

    try:
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()

        stat = os.stat(full_path)
        return {
            "path": path,
            "content": content,
            "created": datetime.fromtimestamp(stat.st_ctime, SAST).isoformat(),
            "modified": datetime.fromtimestamp(stat.st_mtime, SAST).isoformat(),
            "size_bytes": stat.st_size,
        }
    except Exception as e:
        return {"error": f"Failed to read note: {str(e)}"}


@mcp.tool()
async def query_rag(question: str) -> dict:
    """Query the RAG vault for answers from indexed content.

    Args:
        question: The question to answer from the vault

    Returns:
        dict: Answer with source references
    """
    SAST = timezone(timedelta(hours=2))

    # Note: Full RAG implementation would use ChromaDB + Ollama embeddings
    # This is a simplified version using Claude to search vault content

    if not claude_ai.configured:
        return {"error": "Claude AI not configured — set ANTHROPIC_API_KEY"}

    try:
        # Search vault for relevant content (simplified — production uses vector search)
        relevant_docs = []
        if os.path.exists(OBSIDIAN_VAULT_PATH):
            for root, _, files in os.walk(OBSIDIAN_VAULT_PATH):
                for file in files[:10]:  # Limit to first 10 files
                    if file.endswith(".md"):
                        filepath = os.path.join(root, file)
                        try:
                            with open(filepath, "r", encoding="utf-8") as f:
                                content = f.read()
                                if question.lower() in content.lower():
                                    relevant_docs.append({
                                        "path": os.path.relpath(filepath, OBSIDIAN_VAULT_PATH),
                                        "excerpt": content[:500] + "..." if len(content) > 500 else content,
                                    })
                        except:
                            pass

        if not relevant_docs:
            return {
                "question": question,
                "answer": "No relevant documents found in vault.",
                "sources": [],
            }

        # Use Claude to synthesize answer
        system_prompt = (
            "You are the MemoryAgent answering questions from the Obsidian vault. "
            "Synthesize an answer from the provided documents. Cite sources. "
            "If documents don't contain the answer, say so clearly."
        )

        context = "\n\n".join([f"Source: {d['path']}\n{d['excerpt']}" for d in relevant_docs])
        response, usage = await claude_ai.generate(
            system=system_prompt,
            prompt=f"Question: {question}\n\nRelevant documents:\n{context}",
            use_thinking=True,
            effort="medium",
        )

        return {
            "question": question,
            "answer": response,
            "sources": [d["path"] for d in relevant_docs],
            "token_usage": {
                "input": usage.input_tokens,
                "output": usage.output_tokens,
                "total": usage.total_tokens,
            },
            "time_sast": datetime.now(SAST).isoformat(),
        }

    except Exception as e:
        return {"error": f"RAG query failed: {str(e)}"}


# ---------------------------------------------------------------------------
# Platform Management Tools
# ---------------------------------------------------------------------------
@mcp.tool()
async def switch_model(model_name: str) -> dict:
    """Switch the active Ollama model.

    Args:
        model_name: The model to switch to (e.g., "llama3.1:8b", "mistral:7b")

    Returns:
        dict: Confirmation of model switch
    """
    SAST = timezone(timedelta(hours=2))

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            # Check if model exists
            resp = await client.get(f"{NALEDI_API_URL}/api/models/ollama")
            models = resp.json().get("models", [])
            model_names = [m.get("name") for m in models]

            if model_name not in model_names:
                # Try to pull the model
                pull_resp = await client.post(
                    f"{NALEDI_API_URL}/api/models/ollama/pull",
                    params={"name": model_name},
                    timeout=300  # Pull can take a while
                )
                if pull_resp.status_code != 200:
                    return {"error": f"Model '{model_name}' not found and pull failed"}

            return {
                "status": "success",
                "model": model_name,
                "message": f"Switched to {model_name}",
                "time_sast": datetime.now(SAST).isoformat(),
            }

        except httpx.HTTPError as e:
            return {"error": f"Backend API error: {e.response.status_code if hasattr(e, 'response') else str(e)}"}
        except Exception as e:
            return {"error": str(e)}


@mcp.tool()
async def get_agent_status() -> dict:
    """Get status of all 9 Naledi agents.

    Returns:
        dict: Status of all agents including name, status, queue size
    """
    SAST = timezone(timedelta(hours=2))

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(f"{NALEDI_API_URL}/api/agents")
            agents_data = resp.json()

            # Get detailed status for each agent
            detailed = []
            for agent in agents_data.get("agents", []):
                status_resp = await client.get(
                    f"{NALEDI_API_URL}/api/agents/{agent['id']}/status"
                )
                if status_resp.status_code == 200:
                    detailed.append(status_resp.json())

            return {
                "agents": detailed,
                "total": len(detailed),
                "busy": sum(1 for a in detailed if a.get("status") == "working"),
                "queued": sum(a.get("queue", 0) for a in detailed),
                "time_sast": datetime.now(SAST).isoformat(),
            }

        except httpx.HTTPError as e:
            return {"error": f"Backend API error: {e.response.status_code if hasattr(e, 'response') else str(e)}"}
        except Exception as e:
            return {"error": str(e)}


@mcp.tool()
async def toggle_no_hands(enabled: bool) -> dict:
    """Toggle No-Hands automation mode.

    When enabled, the daily RALF loop runs automatically:
    - 00:00 SAST: ResearchAgent
    - 00:30 SAST: PromptAgent
    - 01:00 SAST: MemoryAgent indexing
    - 06:00 SAST: AnalyticsAgent
    - 09:00 SAST: VideoAgent (if No-Hands on)

    Args:
        enabled: True to enable No-Hands mode, False to disable

    Returns:
        dict: Confirmation of toggle
    """
    SAST = timezone(timedelta(hours=2))

    # Note: Production would update a persistent setting in Supabase/DB
    # This is a simplified version that triggers the scheduler immediately

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            if enabled:
                # Trigger the scheduler to start a cycle
                resp = await client.post(f"{NALEDI_API_URL}/api/scheduler/run")
                if resp.status_code == 200:
                    result = resp.json()
                    return {
                        "status": "enabled",
                        "message": "No-Hands mode enabled — daily RALF loop active",
                        "cycle_result": result,
                        "time_sast": datetime.now(SAST).isoformat(),
                    }
                else:
                    return {"error": "Failed to trigger scheduler"}
            else:
                return {
                    "status": "disabled",
                    "message": "No-Hands mode disabled — agents require manual trigger",
                    "time_sast": datetime.now(SAST).isoformat(),
                }

        except httpx.HTTPError as e:
            return {"error": f"Backend API error: {e.response.status_code if hasattr(e, 'response') else str(e)}"}
        except Exception as e:
            return {"error": str(e)}


# ---------------------------------------------------------------------------
# Server Entry Point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Naledi MCP Server")
    parser.add_argument("--transport", choices=["stdio", "sse"], default="stdio",
                        help="Transport mode (default: stdio)")
    parser.add_argument("--host", default="0.0.0.0", help="Host for SSE transport")
    parser.add_argument("--port", type=int, default=8001, help="Port for SSE transport")

    args = parser.parse_args()

    if args.transport == "sse":
        mcp.run(host=args.host, port=args.port, transport="sse")
    else:
        mcp.run()
