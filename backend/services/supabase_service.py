"""Supabase Service — PostgreSQL database, auth, storage, and real-time."""

import os
import httpx
from typing import Optional


class SupabaseService:
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL", "")
        self.key = os.getenv("SUPABASE_SERVICE_KEY", "")
        self.headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
        }

    @property
    def configured(self) -> bool:
        return bool(self.url and self.key)

    async def query(self, table: str, params: Optional[dict] = None) -> list[dict]:
        """Query a Supabase table via REST API."""
        if not self.configured:
            return []
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{self.url}/rest/v1/{table}",
                headers=self.headers,
                params=params or {},
            )
            resp.raise_for_status()
            return resp.json()

    async def insert(self, table: str, data: dict) -> dict:
        """Insert a row into a Supabase table."""
        if not self.configured:
            return {"error": "Supabase not configured"}
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{self.url}/rest/v1/{table}",
                headers={**self.headers, "Prefer": "return=representation"},
                json=data,
            )
            resp.raise_for_status()
            result = resp.json()
            return result[0] if result else {}

    async def update(self, table: str, match: dict, data: dict) -> dict:
        """Update rows matching conditions."""
        if not self.configured:
            return {"error": "Supabase not configured"}
        params = {f"{k}": f"eq.{v}" for k, v in match.items()}
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.patch(
                f"{self.url}/rest/v1/{table}",
                headers={**self.headers, "Prefer": "return=representation"},
                params=params,
                json=data,
            )
            resp.raise_for_status()
            result = resp.json()
            return result[0] if result else {}

    async def delete(self, table: str, match: dict) -> bool:
        """Delete rows matching conditions."""
        if not self.configured:
            return False
        params = {f"{k}": f"eq.{v}" for k, v in match.items()}
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.delete(
                f"{self.url}/rest/v1/{table}",
                headers=self.headers,
                params=params,
            )
            return resp.status_code == 204 or resp.status_code == 200

    async def health(self) -> dict:
        """Check Supabase connection."""
        if not self.configured:
            return {"status": "not_configured"}
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{self.url}/rest/v1/", headers=self.headers)
                return {"status": "connected", "code": resp.status_code}
        except Exception as e:
            return {"status": "error", "detail": str(e)}
