"""Postiz Service — Free self-hosted social media publishing.

Postiz is an open-source alternative to Buffer/Hootsuite.
Self-host for unlimited accounts at zero cost.

Features:
- Instagram, Facebook, LinkedIn, TikTok, Twitter, YouTube, Pinterest
- Schedule posts with media
- AI-generated captions
- Analytics tracking
"""

import os
import httpx
from typing import Optional, Dict, List, Any
from datetime import datetime


class PostizService:
    """Postiz self-hosted social media publisher."""

    def __init__(self):
        self.base_url = os.getenv("POSTIZ_URL", "http://localhost:3000")
        self.api_key = os.getenv("POSTIZ_API_KEY", "")

    async def create_post(
        self,
        content: str,
        platforms: List[str],
        media_urls: Optional[List[str]] = None,
        scheduled_at: Optional[datetime] = None,
        hashtags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a social media post across platforms.

        Args:
            content: Post text/caption
            platforms: List of platforms (instagram, facebook, linkedin, tiktok, twitter, youtube)
            media_urls: Optional list of media URLs
            scheduled_at: Optional scheduled time (UTC)
            hashtags: Optional list of hashtags to append

        Returns:
            Dict with post IDs per platform
        """
        async with httpx.AsyncClient() as client:
            payload = {
                "content": content,
                "platforms": platforms,
                "media": media_urls or [],
                "hashtags": hashtags or [],
            }

            if scheduled_at:
                payload["scheduled_at"] = scheduled_at.isoformat()

            response = await client.post(
                f"{self.base_url}/api/v1/posts",
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"}
            )

            return response.json()

    async def schedule_week(
        self,
        posts: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Schedule a week's worth of posts at optimal times.

        Optimal SAST times: 7AM, 12PM, 3PM, 6PM, 9PM

        Args:
            posts: List of {content, platforms, media}

        Returns:
            List of scheduled post results
        """
        optimal_times = [7, 12, 15, 18, 21]  # SAST hours
        results = []

        for i, post in enumerate(posts):
            day = i // 5
            hour = optimal_times[i % 5]
            scheduled = datetime.utcnow().replace(
                hour=hour - 2,  # UTC offset
                minute=0,
                second=0
            )
            scheduled = scheduled.replace(day=scheduled.day + day)

            result = await self.create_post(
                content=post["content"],
                platforms=post.get("platforms", ["instagram", "facebook"]),
                media_urls=post.get("media"),
                scheduled_at=scheduled,
                hashtags=post.get("hashtags", [])
            )
            results.append(result)

        return results

    async def get_analytics(
        self,
        post_id: Optional[str] = None,
        platform: Optional[str] = None,
        days: int = 7
    ) -> Dict[str, Any]:
        """Get analytics for posts.

        Args:
            post_id: Specific post ID (optional)
            platform: Filter by platform (optional)
            days: Number of days to look back

        Returns:
            Dict with engagement metrics
        """
        async with httpx.AsyncClient() as client:
            params = {"days": days}
            if post_id:
                params["post_id"] = post_id
            if platform:
                params["platform"] = platform

            response = await client.get(
                f"{self.base_url}/api/v1/analytics",
                params=params,
                headers={"Authorization": f"Bearer {self.api_key}"}
            )

            return response.json()


# Alternative: Metricool free tier integration
class MetricoolService:
    """Metricool free tier (1 brand, limited posts)."""

    def __init__(self):
        self.api_key = os.getenv("METRICOOL_API_KEY", "")
        self.base_url = "https://api.metricool.com/v2"

    async def schedule_post(
        self,
        content: str,
        platform: str,
        media_url: str,
        scheduled_time: datetime
    ) -> Dict:
        """Schedule a post via Metricool."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/scheduler",
                json={
                    "text": content,
                    "platform": platform,
                    "media": media_url,
                    "date": scheduled_time.isoformat()
                },
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            return response.json()


# Local content generation with Ollama
class LocalContentGenerator:
    """Generate social content with local models."""

    def __init__(self):
        self.ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = "llama3.1:8b"  # Default content model

    async def generate_caption(
        self,
        topic: str,
        platform: str,
        tone: str = "professional",
        include_emojis: bool = True,
        include_hashtags: bool = True
    ) -> Dict[str, str]:
        """Generate social media caption using local LLM.

        Args:
            topic: What to post about
            platform: Target platform (instagram, linkedin, twitter, etc.)
            tone: Tone (professional, casual, playful, educational)
            include_emojis: Add emojis
            include_hashtags: Add hashtags

        Returns:
            Dict with caption, hashtags, and suggested_media
        """
        prompt = f"""Generate a {platform} post about: {topic}

Tone: {tone}
Platform: {platform}

Create:
1. A compelling caption (under 280 chars for Twitter, under 2200 for Instagram)
2. 5-10 relevant hashtags
3. A description of an ideal image/video for this post

Format your response as:
CAPTION: [your caption here]
HASHTAGS: [hashtags separated by spaces]
MEDIA_SUGGESTION: [brief description of ideal media]
"""

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                }
            )

            result = response.json()
            text = result.get("response", "")

            # Parse response
            lines = text.split("\n")
            caption = ""
            hashtags = ""
            media_suggestion = ""

            for line in lines:
                if line.startswith("CAPTION:"):
                    caption = line.replace("CAPTION:", "").strip()
                elif line.startswith("HASHTAGS:"):
                    hashtags = line.replace("HASHTAGS:", "").strip()
                elif line.startswith("MEDIA_SUGGESTION:"):
                    media_suggestion = line.replace("MEDIA_SUGGESTION:", "").strip()

            return {
                "caption": caption,
                "hashtags": hashtags,
                "media_suggestion": media_suggestion
            }

    async def generate_content_calendar(
        self,
        brand: str,
        week_theme: str,
        platforms: List[str] = ["instagram", "facebook"]
    ) -> List[Dict]:
        """Generate a week's worth of content.

        Args:
            brand: Brand name
            week_theme: Theme for the week
            platforms: Target platforms

        Returns:
            List of 7 content items with captions and hashtags
        """
        prompt = f"""Create a 7-day content calendar for {brand}.

Theme: {week_theme}
Platforms: {', '.join(platforms)}

For each day, provide:
- Day of week
- Post topic
- Caption (platform-optimized)
- Hashtags
- Best time to post (SAST)

Format as JSON array.
"""

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                }
            )

            return response.json()