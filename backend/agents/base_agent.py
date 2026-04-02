"""Base agent class — all 9 Naledi agents inherit from this."""

from datetime import datetime, timezone, timedelta

SAST = timezone(timedelta(hours=2))


class BaseAgent:
    name: str = "BaseAgent"
    description: str = "Base agent"
    status: str = "idle"  # idle | working | error
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
        raise NotImplementedError
