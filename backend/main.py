"""
Naledi Intelligence Platform — Studex Meat
FastAPI backend with all routes, WebSocket support, agent orchestration.
All times SAST. All costs ZAR.
"""

import os
import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from services.ollama_service import OllamaService
from services.context_compressor import ContextCompressor
from services.ralf_gium_scheduler import RALFGIUMScheduler
from services.supabase_service import SupabaseService
from services.firecrawl_service import FirecrawlService
from services.playwright_service import PlaywrightService
from services.claude_service import ClaudeService
from services.higgsfield_service import HiggsFieldService
from agents import (
    ContentAgent, CampaignAgent, AudienceAgent, SEOAgent,
    SocialAgent, EmailAgent, AnalyticsAgent, BrandAgent, ResearchAgent,
)

load_dotenv()

SAST = timezone(timedelta(hours=2))

app = FastAPI(
    title="Naledi Intelligence Platform",
    description="AI-powered marketing intelligence for Studex Meat",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Services
# ---------------------------------------------------------------------------
ollama = OllamaService(base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
compressor = ContextCompressor()
scheduler = RALFGIUMScheduler()
supabase = SupabaseService()
firecrawl = FirecrawlService()
playwright = PlaywrightService()
claude_ai = ClaudeService()
higgsfield = HiggsFieldService()

# ---------------------------------------------------------------------------
# Agent registry
# ---------------------------------------------------------------------------
AGENTS: dict[str, object] = {
    "content": ContentAgent(),
    "campaign": CampaignAgent(),
    "audience": AudienceAgent(),
    "seo": SEOAgent(),
    "social": SocialAgent(),
    "email": EmailAgent(),
    "analytics": AnalyticsAgent(),
    "brand": BrandAgent(),
    "research": ResearchAgent(),
}

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------
class CommandRequest(BaseModel):
    command: str
    context: Optional[dict] = None

class AgentTaskRequest(BaseModel):
    agent: str
    task: str
    priority: str = "normal"  # low | normal | high | critical
    context: Optional[dict] = None

class TokenCalcRequest(BaseModel):
    model: str
    tokens_per_day: int
    days: int = 30

class VideoGenRequest(BaseModel):
    model: str  # kling-3.0 | wan-2.5 | ltx-video
    prompt: str
    duration: int = 5
    aspect_ratio: str = "16:9"

class ScrapeRequest(BaseModel):
    url: str
    mode: str = "scrape"  # scrape | crawl | screenshot | prices | social

class SearchRequest(BaseModel):
    query: str
    limit: int = 5

class TaskBoardItem(BaseModel):
    title: str
    agent: Optional[str] = None
    priority: str = "Medium"  # High | Medium | Low
    column: str = "ASSIGNED"  # ASSIGNED | BUSY | APPROVAL | DONE
    type: Optional[str] = None

class TaskBoardUpdate(BaseModel):
    title: Optional[str] = None
    agent: Optional[str] = None
    priority: Optional[str] = None
    column: Optional[str] = None
    type: Optional[str] = None

# ---------------------------------------------------------------------------
# In-memory task board (persists while server runs)
# ---------------------------------------------------------------------------
TASK_BOARD: dict[str, dict] = {}

def _new_task(title: str, agent: str | None = None, priority: str = "Medium",
              column: str = "ASSIGNED", task_type: str | None = None) -> dict:
    task_id = uuid.uuid4().hex[:8]
    now = datetime.now(SAST)
    task = {
        "id": task_id, "title": title, "agent": agent,
        "priority": priority, "column": column, "type": task_type,
        "created": now.isoformat(), "elapsed": None,
    }
    TASK_BOARD[task_id] = task
    return task

# ---------------------------------------------------------------------------
# Health & info
# ---------------------------------------------------------------------------
@app.get("/")
async def root():
    return {
        "platform": "Naledi Intelligence Platform",
        "client": "Studex Meat",
        "version": "1.0.0",
        "time_sast": datetime.now(SAST).isoformat(),
    }

@app.get("/api/health")
async def health():
    ollama_ok = await ollama.health()
    supa_health = await supabase.health()
    higgs_health = await higgsfield.health()
    return {
        "status": "operational",
        "ollama": "connected" if ollama_ok else "offline",
        "claude": "configured" if claude_ai.configured else "needs ANTHROPIC_API_KEY",
        "higgsfield": higgs_health.get("status", "unknown"),
        "supabase": supa_health.get("status", "unknown"),
        "firecrawl": "configured" if firecrawl.configured else "needs key",
        "playwright": "ready",
        "agents_loaded": len(AGENTS),
        "time_sast": datetime.now(SAST).isoformat(),
    }

# ---------------------------------------------------------------------------
# Command shell — Rulofo GSD endpoint
# ---------------------------------------------------------------------------
@app.post("/api/command")
async def execute_command(req: CommandRequest):
    """Conway-style command shell — parse and route to agents."""
    cmd = req.command.strip()
    compressed = compressor.compress(cmd, req.context)

    # Route to best agent
    agent_name = _route_command(cmd)
    agent = AGENTS.get(agent_name)
    if not agent:
        return {"error": f"No agent matched for command", "input": cmd}

    result = await agent.execute(compressed)
    return {
        "agent": agent_name,
        "result": result,
        "time_sast": datetime.now(SAST).isoformat(),
    }

# ---------------------------------------------------------------------------
# Agents
# ---------------------------------------------------------------------------
@app.get("/api/agents")
async def list_agents():
    return {
        "agents": [
            {"id": k, "name": v.name, "status": v.status, "description": v.description}
            for k, v in AGENTS.items()
        ]
    }

@app.post("/api/agents/task")
async def create_agent_task(req: AgentTaskRequest):
    agent = AGENTS.get(req.agent)
    if not agent:
        raise HTTPException(404, f"Agent '{req.agent}' not found")

    compressed = compressor.compress(req.task, req.context)
    result = await agent.execute(compressed)
    return {
        "agent": req.agent,
        "priority": req.priority,
        "result": result,
        "time_sast": datetime.now(SAST).isoformat(),
    }

@app.get("/api/agents/{agent_id}/status")
async def agent_status(agent_id: str):
    agent = AGENTS.get(agent_id)
    if not agent:
        raise HTTPException(404, f"Agent '{agent_id}' not found")
    return {"id": agent_id, "name": agent.name, "status": agent.status, "queue": agent.queue_size}

# ---------------------------------------------------------------------------
# Ollama models
# ---------------------------------------------------------------------------
@app.get("/api/models/ollama")
async def list_ollama_models():
    models = await ollama.list_models()
    return {"source": "ollama", "models": models}

@app.post("/api/models/ollama/pull")
async def pull_ollama_model(name: str = Query(...)):
    result = await ollama.pull_model(name)
    return {"status": "pulling", "model": name, "result": result}

@app.get("/api/models/ollama/{model}/info")
async def ollama_model_info(model: str):
    info = await ollama.model_info(model)
    return info

# ---------------------------------------------------------------------------
# fal.ai video models
# ---------------------------------------------------------------------------
FAL_MODELS = {
    "kling-3.0": {"name": "Kling 3.0", "endpoint": "fal-ai/kling-video/v3/standard/text-to-video"},
    "wan-2.5": {"name": "Wan 2.5", "endpoint": "fal-ai/wan/v2.5/text-to-video"},
    "ltx-video": {"name": "LTX-Video", "endpoint": "fal-ai/ltx-video"},
}

@app.get("/api/models/video")
async def list_video_models():
    return {"source": "fal.ai", "models": [
        {"id": k, "name": v["name"], "endpoint": v["endpoint"]} for k, v in FAL_MODELS.items()
    ]}

@app.post("/api/models/video/generate")
async def generate_video(req: VideoGenRequest):
    import httpx
    fal_key = os.getenv("FAL_API_KEY")
    if not fal_key:
        raise HTTPException(400, "FAL_API_KEY not configured")

    model_cfg = FAL_MODELS.get(req.model)
    if not model_cfg:
        raise HTTPException(404, f"Video model '{req.model}' not found")

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            f"https://queue.fal.run/{model_cfg['endpoint']}",
            headers={"Authorization": f"Key {fal_key}", "Content-Type": "application/json"},
            json={"prompt": req.prompt, "duration": req.duration, "aspect_ratio": req.aspect_ratio},
        )
        return {"status": "queued", "model": req.model, "response": resp.json()}

# ---------------------------------------------------------------------------
# Higgsfield — AI video generation
# ---------------------------------------------------------------------------
@app.post("/api/video/higgsfield/generate")
async def higgsfield_generate_video(req: VideoGenRequest):
    result = await higgsfield.generate_video(req.prompt, req.duration, req.aspect_ratio)
    return {"source": "higgsfield", "result": result}

@app.get("/api/video/higgsfield/{video_id}")
async def higgsfield_video_status(video_id: str):
    return await higgsfield.get_video_status(video_id)

@app.get("/api/video/higgsfield")
async def higgsfield_list_videos():
    return await higgsfield.list_videos()

# ---------------------------------------------------------------------------
# Token calculator — costs in ZAR
# ---------------------------------------------------------------------------
# ZAR exchange rate approximation (updated manually)
USD_TO_ZAR = 18.50

TOKEN_PRICING = {
    # Ollama local models — free
    "llama3.1:8b": {"input": 0, "output": 0, "local": True},
    "llama3.1:70b": {"input": 0, "output": 0, "local": True},
    "mistral:7b": {"input": 0, "output": 0, "local": True},
    "codestral:22b": {"input": 0, "output": 0, "local": True},
    "deepseek-r1:8b": {"input": 0, "output": 0, "local": True},
    # Cloud models — USD per 1M tokens
    "claude-sonnet-4-6": {"input": 3.0, "output": 15.0, "local": False},
    "claude-haiku-4-5": {"input": 0.80, "output": 4.0, "local": False},
    "claude-opus-4-6": {"input": 15.0, "output": 75.0, "local": False},
    "gpt-4o": {"input": 2.50, "output": 10.0, "local": False},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60, "local": False},
}

@app.get("/api/tokens/pricing")
async def token_pricing():
    zar_pricing = {}
    for model, p in TOKEN_PRICING.items():
        zar_pricing[model] = {
            "input_per_1m_zar": round(p["input"] * USD_TO_ZAR, 2),
            "output_per_1m_zar": round(p["output"] * USD_TO_ZAR, 2),
            "local": p["local"],
        }
    return {"usd_to_zar": USD_TO_ZAR, "pricing": zar_pricing}

@app.post("/api/tokens/calculate")
async def calculate_tokens(req: TokenCalcRequest):
    pricing = TOKEN_PRICING.get(req.model)
    if not pricing:
        raise HTTPException(404, f"Model '{req.model}' not in pricing table")

    daily_cost_usd = (req.tokens_per_day / 1_000_000) * (pricing["input"] + pricing["output"]) / 2
    total_cost_usd = daily_cost_usd * req.days
    return {
        "model": req.model,
        "tokens_per_day": req.tokens_per_day,
        "days": req.days,
        "daily_cost_zar": round(daily_cost_usd * USD_TO_ZAR, 2),
        "weekly_cost_zar": round(daily_cost_usd * 7 * USD_TO_ZAR, 2),
        "monthly_cost_zar": round(daily_cost_usd * 30 * USD_TO_ZAR, 2),
        "total_cost_zar": round(total_cost_usd * USD_TO_ZAR, 2),
        "local": pricing["local"],
    }

# ---------------------------------------------------------------------------
# Task Board — Kanban CRUD
# ---------------------------------------------------------------------------
@app.get("/api/tasks")
async def list_tasks(column: Optional[str] = None):
    tasks = list(TASK_BOARD.values())
    if column:
        tasks = [t for t in tasks if t["column"] == column]
    return {"tasks": tasks}

@app.post("/api/tasks")
async def create_task(req: TaskBoardItem):
    task = _new_task(req.title, req.agent, req.priority, req.column, req.type)
    return task

@app.patch("/api/tasks/{task_id}")
async def update_task(task_id: str, req: TaskBoardUpdate):
    task = TASK_BOARD.get(task_id)
    if not task:
        raise HTTPException(404, f"Task '{task_id}' not found")
    for field in ["title", "agent", "priority", "column", "type"]:
        val = getattr(req, field, None)
        if val is not None:
            task[field] = val
    return task

@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: str):
    if task_id not in TASK_BOARD:
        raise HTTPException(404, f"Task '{task_id}' not found")
    del TASK_BOARD[task_id]
    return {"deleted": task_id}

@app.post("/api/tasks/{task_id}/execute")
async def execute_task(task_id: str):
    """Move task to BUSY, run its agent, then move to DONE."""
    task = TASK_BOARD.get(task_id)
    if not task:
        raise HTTPException(404, f"Task '{task_id}' not found")
    agent_key = task.get("agent", "").lower().replace("agent", "").strip()
    # Try to match agent key
    agent = AGENTS.get(agent_key)
    if not agent:
        # Try fuzzy match
        for k, v in AGENTS.items():
            if k in agent_key or agent_key in k or agent_key in v.name.lower():
                agent = v
                agent_key = k
                break
    if not agent:
        raise HTTPException(400, f"No agent matched for '{task.get('agent')}'")

    task["column"] = "BUSY"
    result = await agent.execute(task["title"])
    task["column"] = "DONE"
    return {"task": task, "result": result}

# ---------------------------------------------------------------------------
# Firecrawl — web scraping & intelligence
# ---------------------------------------------------------------------------
@app.post("/api/scrape")
async def scrape(req: ScrapeRequest):
    """Unified scrape endpoint — Firecrawl for static, Playwright for JS-rendered."""
    if req.mode == "scrape":
        result = await firecrawl.scrape_url(req.url)
        if result.get("error") and "not configured" in result["error"]:
            result = await playwright.scrape_rendered(req.url)
        return result
    elif req.mode == "crawl":
        return await firecrawl.crawl_site(req.url)
    elif req.mode == "screenshot":
        return await playwright.screenshot(req.url)
    elif req.mode == "prices":
        return await playwright.extract_prices(req.url)
    elif req.mode == "social":
        return await playwright.monitor_social(req.url)
    else:
        raise HTTPException(400, f"Unknown scrape mode: {req.mode}")

@app.post("/api/search")
async def search_web(req: SearchRequest):
    """Search the web via Firecrawl."""
    return await firecrawl.search(req.query, req.limit)

@app.get("/api/scrape/status")
async def scrape_status():
    return {
        "firecrawl": "configured" if firecrawl.configured else "needs FIRECRAWL_API_KEY",
        "playwright": "ready",
    }

# ---------------------------------------------------------------------------
# RALF-GIUM scheduler
# ---------------------------------------------------------------------------
@app.get("/api/scheduler/tasks")
async def list_scheduled_tasks():
    return {"tasks": scheduler.list_tasks()}

@app.post("/api/scheduler/run")
async def trigger_scheduler():
    results = await scheduler.run_cycle(AGENTS)
    return {"cycle": "complete", "results": results, "time_sast": datetime.now(SAST).isoformat()}

# ---------------------------------------------------------------------------
# WebSocket — live agent feed
# ---------------------------------------------------------------------------
connected_clients: list[WebSocket] = []

@app.websocket("/ws/agents")
async def agent_feed(ws: WebSocket):
    await ws.accept()
    connected_clients.append(ws)
    try:
        while True:
            data = await ws.receive_text()
            msg = json.loads(data)
            agent_name = msg.get("agent")
            agent = AGENTS.get(agent_name)
            if agent:
                result = await agent.execute(msg.get("task", ""))
                await ws.send_json({"agent": agent_name, "result": result, "time_sast": datetime.now(SAST).isoformat()})
            else:
                await ws.send_json({"error": f"Unknown agent: {agent_name}"})
    except WebSocketDisconnect:
        connected_clients.remove(ws)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _route_command(cmd: str) -> str:
    """Simple keyword-based routing to agents."""
    cmd_lower = cmd.lower()
    routing = {
        "content": ["write", "copy", "blog", "post", "article", "headline", "content"],
        "campaign": ["campaign", "launch", "schedule", "automate", "workflow"],
        "audience": ["audience", "segment", "persona", "target", "demographic"],
        "seo": ["seo", "keyword", "rank", "search", "meta", "backlink"],
        "social": ["social", "twitter", "instagram", "facebook", "linkedin", "tiktok"],
        "email": ["email", "newsletter", "subject line", "drip", "sequence"],
        "analytics": ["analytics", "metric", "report", "dashboard", "performance", "roi"],
        "brand": ["brand", "voice", "tone", "guideline", "identity", "logo"],
        "research": ["research", "competitor", "market", "trend", "industry", "analyze"],
    }
    for agent_name, keywords in routing.items():
        if any(kw in cmd_lower for kw in keywords):
            return agent_name
    return "content"  # default fallback


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
