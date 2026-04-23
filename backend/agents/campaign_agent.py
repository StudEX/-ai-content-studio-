"""Campaign Manager Agent — orchestrates campaigns powered by Claude AI."""

from .base_agent import BaseAgent


class CampaignAgent(BaseAgent):
    name = "Campaign Manager"
    description = "Orchestrates campaign creation, scheduling, A/B testing, and multi-channel delivery."
    system_prompt = (
        "You are the Campaign Manager agent for Studex Meat. "
        "You plan and orchestrate multi-channel marketing campaigns across email, social media, SMS, and web. "
        "You create campaign briefs, suggest A/B test variants, define target audiences, "
        "and build scheduling timelines. All times in SAST. All costs in ZAR. "
        "Focus on ROI and measurable outcomes."
    )
