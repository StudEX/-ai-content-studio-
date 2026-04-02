"""Ollama Service — manages local LLM models via Ollama API."""

import httpx
from typing import Optional


class OllamaService:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url.rstrip("/")

    async def health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(self.base_url)
                return resp.status_code == 200
        except Exception:
            return False

    async def list_models(self) -> list[dict]:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                data = resp.json()
                return [
                    {
                        "name": m["name"],
                        "size": m.get("size", 0),
                        "modified_at": m.get("modified_at", ""),
                        "digest": m.get("digest", "")[:12],
                    }
                    for m in data.get("models", [])
                ]
        except Exception:
            return []

    async def pull_model(self, name: str) -> dict:
        try:
            async with httpx.AsyncClient(timeout=300) as client:
                resp = await client.post(
                    f"{self.base_url}/api/pull",
                    json={"name": name, "stream": False},
                )
                return resp.json()
        except Exception as e:
            return {"error": str(e)}

    async def model_info(self, name: str) -> dict:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    f"{self.base_url}/api/show",
                    json={"name": name},
                )
                return resp.json()
        except Exception as e:
            return {"error": str(e)}

    async def generate(self, model: str, prompt: str, system: Optional[str] = None) -> str:
        payload = {"model": model, "prompt": prompt, "stream": False}
        if system:
            payload["system"] = system
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(f"{self.base_url}/api/generate", json=payload)
                return resp.json().get("response", "")
        except Exception as e:
            return f"[Ollama error] {e}"
