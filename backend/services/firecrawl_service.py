"""
Firecrawl Service — Web scraping and intelligence gathering.
Powers the Research Agent, SEO Agent, and competitive analysis.
"""

import os
from typing import Optional
from firecrawl import FirecrawlApp


class FirecrawlService:
    def __init__(self):
        self.api_key = os.getenv("FIRECRAWL_API_KEY", "")
        self._client: Optional[FirecrawlApp] = None

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    @property
    def client(self) -> FirecrawlApp:
        if not self._client:
            self._client = FirecrawlApp(api_key=self.api_key)
        return self._client

    async def scrape_url(self, url: str, formats: list[str] | None = None) -> dict:
        """Scrape a single URL and return structured content."""
        if not self.configured:
            return {"error": "FIRECRAWL_API_KEY not configured"}
        try:
            result = self.client.scrape_url(
                url,
                params={"formats": formats or ["markdown", "html"]},
            )
            return {
                "url": url,
                "title": result.get("metadata", {}).get("title", ""),
                "description": result.get("metadata", {}).get("description", ""),
                "markdown": result.get("markdown", ""),
                "metadata": result.get("metadata", {}),
            }
        except Exception as e:
            return {"error": str(e), "url": url}

    async def crawl_site(self, url: str, max_pages: int = 10) -> dict:
        """Crawl an entire site — great for competitor analysis."""
        if not self.configured:
            return {"error": "FIRECRAWL_API_KEY not configured"}
        try:
            result = self.client.crawl_url(
                url,
                params={"limit": max_pages, "scrapeOptions": {"formats": ["markdown"]}},
            )
            pages = result.get("data", [])
            return {
                "url": url,
                "pages_crawled": len(pages),
                "pages": [
                    {
                        "url": p.get("metadata", {}).get("sourceURL", ""),
                        "title": p.get("metadata", {}).get("title", ""),
                        "markdown_length": len(p.get("markdown", "")),
                    }
                    for p in pages
                ],
            }
        except Exception as e:
            return {"error": str(e), "url": url}

    async def extract_structured(self, url: str, schema: dict) -> dict:
        """Extract structured data from a page using LLM extraction."""
        if not self.configured:
            return {"error": "FIRECRAWL_API_KEY not configured"}
        try:
            result = self.client.scrape_url(
                url,
                params={
                    "formats": ["extract"],
                    "extract": {"schema": schema},
                },
            )
            return {
                "url": url,
                "extracted": result.get("extract", {}),
            }
        except Exception as e:
            return {"error": str(e), "url": url}

    async def search(self, query: str, limit: int = 5) -> dict:
        """Search the web and return scraped results."""
        if not self.configured:
            return {"error": "FIRECRAWL_API_KEY not configured"}
        try:
            result = self.client.search(query, params={"limit": limit})
            results = result.get("data", []) if isinstance(result, dict) else result
            return {
                "query": query,
                "results": [
                    {
                        "url": r.get("url", ""),
                        "title": r.get("title", ""),
                        "description": r.get("description", ""),
                    }
                    for r in (results if isinstance(results, list) else [])
                ],
            }
        except Exception as e:
            return {"error": str(e), "query": query}
