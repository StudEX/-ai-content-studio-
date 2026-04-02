"""SEO Optimizer Agent — keyword research, meta tags, content optimization.
Uses Firecrawl for page analysis and competitor SEO scraping."""

from .base_agent import BaseAgent


class SEOAgent(BaseAgent):
    name = "SEO Optimizer"
    description = "Performs keyword research, generates meta tags, analyzes competitor SEO, and optimizes content for search rankings. Uses Firecrawl for page analysis."

    async def _run(self, task: str) -> str:
        task_lower = task.lower()

        if any(kw in task_lower for kw in ["analyze", "audit", "check", "url", "http"]):
            return (
                f"[SEO Optimizer] Page analysis task: {task}\n"
                "Ready to analyze via Firecrawl:\n"
                "  • Extract meta tags, headings, structured data\n"
                "  • Check title/description lengths\n"
                "  • Analyze content structure\n"
                "Use POST /api/scrape with mode='scrape' for SEO audit."
            )

        return (
            f"[SEO Optimizer] Task received: {task}\n"
            "Capabilities: Keyword research, meta generation, content scoring, competitor SEO analysis.\n"
            "Tools: Firecrawl (page scraping), structured data extraction."
        )
