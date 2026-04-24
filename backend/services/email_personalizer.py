"""Email Personalizer — Claude writes custom outreach emails per prospect.

StudEx AI Sales Assistant
- Analyzes prospect business
- Writes personalized cold emails
- A/B test different angles
- Tracks performance per template
"""

import os
import json
import re
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from claude_service import ClaudeService, Message


@dataclass
class Prospect:
    """E-commerce prospect for outreach."""
    name: str
    email: str
    company: str
    website: str
    platform: str  # shopify, woocommerce, bigcommerce, etc.
    niche: str  # fashion, electronics, beauty, etc.
    estimated_orders: str  # 0-100, 100-500, 500-1000, 1000+
    social_links: Dict[str, str]
    pain_points: List[str] = None
    notes: str = ""


@dataclass
class PersonalizedEmail:
    """Generated personalized email."""
    prospect_email: str
    subject: str
    body: str
    angle: str  # which value proposition we used
    tone: str  # professional, casual, friendly
    follow_up_schedule: List[int]  # days to follow up [2, 7, 14]
    tokens_used: int = 0
    generated_at: str = ""


class EmailPersonalizer:
    """AI-powered email personalization for sales outreach."""

    # Email angles tested for SA e-commerce
    VALUE_ANGLES = {
        "cs_revenue_recovery": {
            "name": "Customer Service Revenue Recovery",
            "hook": "Stores lose 30% of revenue to slow CS responses",
            "focus": "24/7 instant WhatsApp responses"
        },
        "cart_abandonment": {
            "name": "Cart Abandonment Saver",
            "hook": "60% of carts abandoned, mostly not followed up",
            "focus": "Automated recovery via WhatsApp"
        },
        "support_costs": {
            "name": "Support Cost Reduction",
            "hook": "Hiring CS agents costs R15k+/month",
            "focus": "One bot replaces 3 agents"
        },
        "growth_overflow": {
            "name": "Growth Overflow Handler",
            "hook": "Growth brings too many support tickets",
            "focus": "Scale without hiring"
        },
        "after_hours": {
            "name": "After-Hours Sales Capture",
            "hook": "40% of online shopping happens after 6PM",
            "focus": "Never miss a sale, even at midnight"
        }
    }

    def __init__(self):
        self.claude = ClaudeService()
        self._load_prompts()

    def _load_prompts(self):
        """Load email generation prompts."""
        self.system_prompt = """You are a world-class sales copywriter specializing in B2B SaaS for South African e-commerce.

Your job: Write personalized cold emails that get replies.

RULES:
1. Keep emails under 150 words
2. Lead with a specific observation about THEIR business
3. Show you understand their pain point
4. Offer clear value (one specific benefit)
5. Include one soft CTA (reply, book call, etc.)
6. No generic fluff like "I hope this email finds you well"
7. Use natural, conversational language
8. Mention South Africa/African context when relevant

EMAIL STRUCTURE:
- Subject: Max 50 chars, curiosity-driven
- Hook: 1-2 sentences showing you researched them
- Problem: Their specific pain point
- Solution: How StudEx AI solves it
- CTA: Low-friction next step
- Signature: Brief

TONE GUIDELINES:
- Professional but not corporate
- Friendly but not over-familiar
- Confident but not arrogant"""

    def _analyze_prospect(self, prospect: Prospect) -> Dict:
        """Analyze prospect to determine best angle."""
        # Determine best angle based on prospect data
        if prospect.estimated_orders in ["0-100"]:
            angle = "growth_overflow"
        elif prospect.estimated_orders in ["100-500"]:
            angle = "cs_revenue_recovery"
        elif prospect.estimated_orders in ["500-1000"]:
            angle = "cart_abandonment"
        else:
            angle = "support_costs"

        # Adjust for platform
        if prospect.platform.lower() == "shopify":
            platform_note = "Shopify store with easy integration"
        elif prospect.platform.lower() == "woocommerce":
            platform_note = "WooCommerce store needing WordPress integration"
        else:
            platform_note = f"{prospect.platform} platform"

        return {
            "angle": angle,
            "angle_data": self.VALUE_ANGLES[angle],
            "platform_note": platform_note,
            "company_size": self._size_to_description(prospect.estimated_orders)
        }

    def _size_to_description(self, size: str) -> str:
        """Convert order size to description."""
        mapping = {
            "0-100": "growing store just getting started",
            "100-500": "established store processing regular orders",
            "500-1000": "successful store handling significant volume",
            "1000+": "high-volume operation"
        }
        return mapping.get(size, "growing business")

    async def generate_email(
        self,
        prospect: Prospect,
        tone: str = "professional",
        custom_hook: Optional[str] = None
    ) -> PersonalizedEmail:
        """Generate personalized email for prospect."""

        analysis = self._analyze_prospect(prospect)
        angle_data = analysis["angle_data"]

        # Build prompt
        research_info = f"""
PROSPECT RESEARCH:
- Name: {prospect.name}
- Company: {prospect.company}
- Website: {prospect.website}
- Platform: {analysis['platform_note']}
- Niche: {prospect.niche}
- Size: {analysis['company_size']} ({prospect.estimated_orders} orders/month estimated)
- Social: {json.dumps(prospect.social_links)}
"""
        if prospect.notes:
            research_info += f"\nAdditional Notes: {prospect.notes}"

        if custom_hook:
            research_info += f"\nCustom Hook Angle: {custom_hook}"

        user_prompt = f"""Write a personalized cold email for this South African e-commerce prospect.

{research_info}

VALUE PROPOSITION TO EMPHASIZE:
- {angle_data['hook']}
- {angle_data['focus']}
- Result: More sales, fewer abandoned carts, happier customers

TONE: {tone}

FORMAT YOUR RESPONSE AS JSON:
{{
    "subject": "subject line here (max 50 chars)",
    "body": "email body here (max 150 words, single string with \\n for line breaks)",
    "angle": "which value prop you focused on",
    "follow_up_angles": ["idea for follow-up 1", "idea for follow-up 2"]
}}"""

        # Call Claude
        messages = [
            Message(role="user", content=user_prompt)
        ]

        response, thinking, metrics = await self.claude.chat_with_thinking(
            messages=messages,
            system_prompt=self.system_prompt,
            temperature=0.7
        )

        # Parse response
        try:
            # Extract JSON from response
            json_match = re.search(r'\{[^}]+\}', response, re.DOTALL)
            if json_match:
                email_data = json.loads(json_match.group())
            else:
                # Fallback parsing
                email_data = self._fallback_parse(response)

            return PersonalizedEmail(
                prospect_email=prospect.email,
                subject=email_data.get("subject", ""),
                body=email_data.get("body", ""),
                angle=email_data.get("angle", analysis["angle"]),
                tone=tone,
                follow_up_schedule=[2, 7, 14],
                tokens_used=metrics.total_tokens if metrics else 0,
                generated_at=datetime.now().isoformat()
            )

        except Exception as e:
            print(f"Failed to parse email: {e}")
            return self._generate_fallback_email(prospect, analysis)

    def _fallback_parse(self, response: str) -> Dict:
        """Fallback parsing if JSON fails."""
        lines = response.split('\n')
        subject = ""
        body_lines = []
        in_body = False

        for line in lines:
            if 'subject' in line.lower() and ':' in line:
                subject = line.split(':', 1)[1].strip().strip('"')
            elif 'body' in line.lower():
                in_body = True
            elif in_body and line.strip():
                body_lines.append(line.strip())

        return {
            "subject": subject or "Quick question about your store",
            "body": '\n'.join(body_lines),
            "angle": "general"
        }

    def _generate_fallback_email(self, prospect: Prospect, analysis: Dict) -> PersonalizedEmail:
        """Generate basic email if AI fails."""
        angle_data = analysis["angle_data"]

        subject = f"Quick question about {prospect.company}"

        body = f"""Hi {prospect.name.split()[0]},

I came across {prospect.company} while researching {prospect.niche} stores in South Africa.

{angle_data['hook']}. Most stores handling {prospect.estimated_orders} orders/month struggle with this.

StudEx AI provides {angle_data['focus'].lower()}, answering customer queries instantly via WhatsApp — where 20 million South Africans already shop.

Worth a 10-minute chat to see if it could work for {prospect.company}?

Best,
Tumelo
StudEx AI
https://tumeloramaphosa.com"""

        return PersonalizedEmail(
            prospect_email=prospect.email,
            subject=subject,
            body=body,
            angle=analysis["angle"],
            tone="professional",
            follow_up_schedule=[2, 7, 14],
            generated_at=datetime.now().isoformat()
        )

    async def generate_follow_up(
        self,
        prospect: Prospect,
        original_email: PersonalizedEmail,
        follow_up_number: int
    ) -> str:
        """Generate follow-up email."""

        angles = [
            f"Follow up on my email about {original_email.angle}",
            f"Quick value add: case study from similar {prospect.niche} store",
            f"Last touch: quick question"
        ]

        user_prompt = f"""Write follow-up #{follow_up_number} for this prospect.

ORIGINAL EMAIL:
Subject: {original_email.subject}
Body: {original_email.body}

PROSPECT:
- {prospect.name} at {prospect.company}
- {prospect.niche} store, {prospect.estimated_orders} orders/month

FOLLOW-UP ANGLE: {angles[follow_up_number - 1]}

GUIDELINES:
- Keep it under 100 words
- Be brief and direct
- Add new value (don't just say "checking in")
- Softer CTA than original"""

        messages = [Message(role="user", content=user_prompt)]

        response, _, _ = await self.claude.chat_with_thinking(
            messages=messages,
            system_prompt=self.system_prompt,
            temperature=0.7
        )

        return response

    async def generate_sequence(self, prospect: Prospect) -> List[PersonalizedEmail]:
        """Generate full 4-email sequence for prospect."""
        emails = []

        # Main email
        main = await self.generate_email(prospect)
        emails.append(main)

        # Follow-ups
        for i in range(1, 4):
            follow_up_body = await self.generate_follow_up(prospect, main, i)
            emails.append(PersonalizedEmail(
                prospect_email=prospect.email,
                subject=f"Re: {main.subject}" if i < 3 else f"Should I close your file?",
                body=follow_up_body,
                angle=f"follow_up_{i}",
                tone=main.tone,
                follow_up_schedule=[]
            ))

        return emails

    def get_template_performance(self) -> Dict:
        """Get performance data for each angle."""
        # Placeholder — would connect to real metrics
        return {
            "cs_revenue_recovery": {"sent": 0, "opens": 0, "replies": 0},
            "cart_abandonment": {"sent": 0, "opens": 0, "replies": 0},
            "support_costs": {"sent": 0, "opens": 0, "replies": 0},
            "growth_overflow": {"sent": 0, "opens": 0, "replies": 0},
            "after_hours": {"sent": 0, "opens": 0, "replies": 0}
        }


# Test function
async def test_personalizer():
    """Test email personalization."""
    print("🧪 Testing Email Personalizer...\n")

    personalizer = EmailPersonalizer()

    # Test prospect
    prospect = Prospect(
        name="Sarah Johnson",
        email="sarah@example.co.za",
        company="Example Fashion",
        website="https://example.co.za",
        platform="Shopify",
        niche="fashion",
        estimated_orders="100-500",
        social_links={"instagram": "@examplefashion"},
        notes="Growing Instagram following, likely getting more DMs"
    )

    # Generate email
    email = await personalizer.generate_email(prospect, tone="friendly")

    print(f"📧 Generated Email for {prospect.name}")
    print(f"Subject: {email.subject}")
    print(f"Angle: {email.angle}")
    print(f"Tokens: {email.tokens_used}\n")
    print(f"Body:\n{email.body}\n")
    print("-" * 60)

    return email


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_personalizer())
