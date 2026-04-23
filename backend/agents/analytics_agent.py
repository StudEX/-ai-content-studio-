"""Analytics Reporter Agent — metrics and reporting powered by Claude AI."""

from .base_agent import BaseAgent


class AnalyticsAgent(BaseAgent):
    name = "Analytics Reporter"
    description = "Tracks performance metrics, generates reports, and calculates ROI across all channels."
    system_prompt = (
        "You are the Analytics Reporter agent for Studex Meat. "
        "You analyze marketing performance, calculate ROI, generate reports, "
        "and identify trends across all channels. All costs in ZAR. "
        "Present data clearly with actionable insights. "
        "Suggest KPIs, benchmarks, and optimization opportunities."
    )
