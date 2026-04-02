"""Market Research Agent — competitor analysis, trend tracking, web intelligence.
Powered by Firecrawl (web scraping) and Playwright (JS-rendered pages)."""

from .base_agent import BaseAgent


class ResearchAgent(BaseAgent):
    name = "Market Researcher"
    description = "Conducts competitor analysis, tracks market trends, scrapes competitor sites, and provides industry intelligence. Powered by Firecrawl + Playwright."

    async def _run(self, task: str) -> str:
        task_lower = task.lower()

        if any(kw in task_lower for kw in ["scrape", "crawl", "website", "url", "http"]):
            return (
                f"[Market Researcher] Web scraping task: {task}\n"
                "Ready to scrape via Firecrawl (structured) or Playwright (JS-rendered).\n"
                "Use POST /api/scrape with url and mode (scrape|crawl|screenshot|prices|social)."
            )

        if any(kw in task_lower for kw in ["competitor", "competition", "rival"]):
            return (
                f"[Market Researcher] Competitor analysis: {task}\n"
                "Capabilities:\n"
                "  • Crawl competitor sites (Firecrawl)\n"
                "  • Extract pricing in ZAR (Playwright)\n"
                "  • Screenshot competitor pages (Playwright)\n"
                "  • Monitor social meta tags (Playwright)\n"
                "Use POST /api/scrape or POST /api/search."
            )

        return (
            f"[Market Researcher] Task received: {task}\n"
            "Capabilities: Web search, site crawling, competitor scraping, price extraction, social monitoring.\n"
            "Tools: Firecrawl (API scraping), Playwright (browser automation)."
        )
