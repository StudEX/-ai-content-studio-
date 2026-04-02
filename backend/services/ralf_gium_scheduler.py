"""
RALF-GIUM Scheduler — Rhythmic Agent Loop Framework with
Goal-Integrated Unified Management.

Cycles through agents on a priority-based schedule,
executing queued tasks and maintenance routines.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional

SAST = timezone(timedelta(hours=2))


class ScheduledTask:
    def __init__(self, agent: str, task: str, priority: str = "normal", interval_minutes: int = 60):
        self.agent = agent
        self.task = task
        self.priority = priority
        self.interval_minutes = interval_minutes
        self.last_run: Optional[datetime] = None
        self.run_count = 0

    def is_due(self) -> bool:
        if self.last_run is None:
            return True
        elapsed = (datetime.now(SAST) - self.last_run).total_seconds() / 60
        return elapsed >= self.interval_minutes

    def mark_run(self):
        self.last_run = datetime.now(SAST)
        self.run_count += 1

    def to_dict(self) -> dict:
        return {
            "agent": self.agent,
            "task": self.task,
            "priority": self.priority,
            "interval_minutes": self.interval_minutes,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "run_count": self.run_count,
        }


class RALFGIUMScheduler:
    """Priority-based agent task scheduler."""

    PRIORITY_ORDER = {"critical": 0, "high": 1, "normal": 2, "low": 3}

    def __init__(self):
        self._tasks: list[ScheduledTask] = [
            # Default recurring tasks
            ScheduledTask("analytics", "Generate daily performance summary", "normal", 1440),
            ScheduledTask("brand", "Run brand consistency check", "low", 720),
            ScheduledTask("research", "Scan competitor activity", "normal", 480),
            ScheduledTask("seo", "Update keyword rankings", "normal", 360),
            ScheduledTask("social", "Check engagement metrics", "high", 60),
        ]

    def list_tasks(self) -> list[dict]:
        return [t.to_dict() for t in sorted(
            self._tasks, key=lambda t: self.PRIORITY_ORDER.get(t.priority, 2)
        )]

    def add_task(self, agent: str, task: str, priority: str = "normal", interval: int = 60):
        self._tasks.append(ScheduledTask(agent, task, priority, interval))

    async def run_cycle(self, agents: dict) -> list[dict]:
        """Execute all due tasks in priority order."""
        results = []
        due_tasks = sorted(
            [t for t in self._tasks if t.is_due()],
            key=lambda t: self.PRIORITY_ORDER.get(t.priority, 2),
        )

        for task in due_tasks:
            agent = agents.get(task.agent)
            if not agent:
                results.append({"agent": task.agent, "error": "Agent not found"})
                continue

            result = await agent.execute(task.task)
            task.mark_run()
            results.append({
                "agent": task.agent,
                "task": task.task,
                "result": result,
                "run_count": task.run_count,
            })

        return results
