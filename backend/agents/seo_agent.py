"""SEO Optimizer Agent — search optimization powered by Claude AI + Firecrawl."""

from .base_agent import BaseAgent


class SEOAgent(BaseAgent):
    name = "SEO Optimizer"
    description = "Performs keyword research, generates meta tags, analyzes competitor SEO, and optimizes content. Uses Firecrawl for page analysis."
    system_prompt = (
        "You are the SEO Optimizer agent for Studex Meat. "
        "You perform keyword research, generate meta titles and descriptions, "
        "create content briefs optimized for search, and analyze competitor SEO strategies. "
        "Focus on South African search trends and meat industry keywords. "
        "When given a URL or page content, provide specific SEO recommendations."
    )
