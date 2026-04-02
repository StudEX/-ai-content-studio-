"""Content Creator Agent — generates marketing copy, blog posts, headlines."""

from .base_agent import BaseAgent


class ContentAgent(BaseAgent):
    name = "Content Creator"
    description = "Generates marketing copy, blog posts, headlines, and product descriptions for Studex Meat."

    async def _run(self, task: str) -> str:
        return (
            f"[Content Creator] Task received: {task}\n"
            "Status: Ready to generate content.\n"
            "Capabilities: Blog posts, ad copy, product descriptions, social captions, email copy.\n"
            "Awaiting AI engine connection for full generation."
        )
