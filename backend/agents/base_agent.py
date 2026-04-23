"""Base agent class — all 9 Naledi agents inherit from this.
Each agent gets a Claude AI brain via the Anthropic API."""

from datetime import datetime, timezone, timedelta
from services.claude_service import ClaudeService

SAST = timezone(timedelta(hours=2))

claude = ClaudeService()


class BaseAgent:
    name: str = "BaseAgent"
    description: str = "Base agent"
    system_prompt: str = "You are a helpful marketing AI assistant for Studex Meat."
    status: str = "idle"
    _queue: list[dict] = []

    @property
    def queue_size(self) -> int:
        return len(self._queue)

    async def execute(self, task: str) -> dict:
        self.status = "working"
        try:
            result = await self._run(task)
            self.status = "idle"
            return {
                "agent": self.name,
                "output": result,
                "time_sast": datetime.now(SAST).isoformat(),
            }
        except Exception as e:
            self.status = "error"
            return {"agent": self.name, "error": str(e)}

    async def _run(self, task: str) -> str:
        """Default: send task to Claude with agent's system prompt."""
        return await claude.generate(self.system_prompt, task)
