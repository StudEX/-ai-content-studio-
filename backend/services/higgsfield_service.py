"""Higgsfield Service — AI video generation for Studex Meat marketing content."""

import os
import httpx
from typing import Optional


class HiggsFieldService:
    BASE_URL = "https://api.higgsfield.ai/v1"

    def __init__(self):
        self.api_key = os.getenv("HIGGSFIELD_API_KEY", "")
        self.secret = os.getenv("HIGGSFIELD_SECRET", "")

    @property
    def configured(self) -> bool:
        return bool(self.api_key and self.secret)

    @property
    def headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "X-API-Secret": self.secret,
            "Content-Type": "application/json",
        }

    async def generate_video(self, prompt: str, duration: int = 5, aspect_ratio: str = "16:9") -> dict:
        """Generate a marketing video from a text prompt."""
        if not self.configured:
            return {"error": "Higgsfield not configured — set HIGGSFIELD_API_KEY and HIGGSFIELD_SECRET"}
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(
                    f"{self.BASE_URL}/videos/generate",
                    headers=self.headers,
                    json={
                        "prompt": prompt,
                        "duration": duration,
                        "aspect_ratio": aspect_ratio,
                    },
                )
                return resp.json()
        except Exception as e:
            return {"error": str(e)}

    async def get_video_status(self, video_id: str) -> dict:
        """Check the status of a video generation job."""
        if not self.configured:
            return {"error": "Higgsfield not configured"}
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    f"{self.BASE_URL}/videos/{video_id}",
                    headers=self.headers,
                )
                return resp.json()
        except Exception as e:
            return {"error": str(e)}

    async def list_videos(self, limit: int = 20) -> dict:
        """List generated videos."""
        if not self.configured:
            return {"error": "Higgsfield not configured"}
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    f"{self.BASE_URL}/videos",
                    headers=self.headers,
                    params={"limit": limit},
                )
                return resp.json()
        except Exception as e:
            return {"error": str(e)}

    async def health(self) -> dict:
        """Check Higgsfield API connectivity."""
        if not self.configured:
            return {"status": "not_configured"}
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{self.BASE_URL}/health", headers=self.headers)
                return {"status": "connected", "code": resp.status_code}
        except Exception as e:
            return {"status": "error", "detail": str(e)}
