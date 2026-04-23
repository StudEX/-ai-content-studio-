"""Audience Analyst Agent — segments audiences powered by Claude AI."""

from .base_agent import BaseAgent


class AudienceAgent(BaseAgent):
    name = "Audience Analyst"
    description = "Segments audiences, builds personas, and identifies target demographics for Studex Meat."
    system_prompt = (
        "You are the Audience Analyst agent for Studex Meat. "
        "You analyze customer demographics, build detailed buyer personas, "
        "and create audience segments for targeted marketing. "
        "Focus on the South African market — consider LSM groups, regional preferences, "
        "cultural food traditions, and buying patterns. Output actionable segment definitions."
    )
