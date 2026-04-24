"""Outreach Manager — Orchestrates email campaigns end-to-end.

Flow:
1. Scrape prospects from prospect_scraper.py
2. Enrich with additional data
3. Generate personalized emails with email_personalizer.py
4. Send with rate limiting via email_sender.py
5. Schedule follow-ups
6. Track and report
"""

import asyncio
import json
from typing import List, Dict, Optional
from dataclasses import asdict
from pathlib import Path
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from prospect_scraper import ProspectScraper
from email_personalizer import EmailPersonalizer, Prospect, PersonalizedEmail
from email_sender import EmailSender, EmailCampaign


class OutreachManager:
    """Manages complete outreach workflow."""

    def __init__(self):
        self.scraper = ProspectScraper()
        self.personalizer = EmailPersonalizer()
        self.sender = EmailSender()
        self.data_dir = Path(__file__).parent.parent / "data" / "email_campaigns"
        self.data_dir.mkdir(parents=True, exist_ok=True)

    async def run_campaign(
        self,
        niche: str,
        min_orders: str = "100-500",
        max_prospects: int = 100,
        angle: Optional[str] = None,
        test_mode: bool = True
    ) -> Dict:
        """
        Run complete outreach campaign.

        Args:
            niche: Fashion, electronics, beauty, etc.
            min_orders: Minimum order volume to target
            max_prospects: Max prospects to scrape
            angle: Specific value angle, or auto-select
            test_mode: If True, just preview, don't send

        Returns:
            Campaign results summary
        """
        print("=" * 60)
        print(f"🚀 Starting Outreach Campaign")
        print(f"   Niche: {niche}")
        print(f"   Min orders: {min_orders}")
        print(f"   Max prospects: {max_prospects}")
        print(f"   Mode: {'TEST' if test_mode else 'LIVE'}")
        print("=" * 60)
        print()

        # PHASE 1: Scrape Prospects
        print("📊 PHASE 1: Scraping Prospects...")
        prospects = await self._scrape_prospects(niche, max_prospects)

        if not prospects:
            return {"error": "No prospects found", "phase": "scraping"}

        # Filter by order volume
        order_priority = {"0-100": 1, "100-500": 2, "500-1000": 3, "1000+": 4}
        min_priority = order_priority.get(min_orders, 1)
        prospects = [p for p in prospects if order_priority.get(p.estimated_orders, 0) >= min_priority]

        print(f"   ✓ Filtered to {len(prospects)} prospects (≥{min_orders} orders)")
        print()

        # PHASE 2: Enrich Data (optional - could add more research here)
        print("📊 PHASE 2: Enriching Prospect Data...")
        prospects = await self._enrich_prospects(prospects)
        print(f"   ✓ Enrichment complete")
        print()

        # PHASE 3: Generate Emails
        print("📊 PHASE 3: Generating Personalized Emails...")
        emails = await self._generate_emails(prospects, angle)
        print(f"   ✓ Generated {len(emails)} personalized emails")
        print()

        # PHASE 4: Create Campaign
        campaign = EmailCampaign(
            id=f"{niche.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            name=f"{niche.title()} Outreach - {len(prospects)} Prospects",
            angle=angle or "auto",
            prospects=prospects,
            created_at=datetime.now().isoformat(),
            status="ready"
        )

        # PHASE 5: Send (or preview)
        print("📊 PHASE 4: Sending Emails...")

        if test_mode:
            results = await self._preview_campaign(campaign, emails, prospects)
        else:
            # Check we can send
            can_send, msg = self.sender.can_send_today(len(prospects))
            if not can_send:
                print(f"   ❌ {msg}")
                return {"error": msg, "phase": "sending"}

            results = await self.sender.send_campaign(campaign, emails, test_mode=False)

        print()
        print("=" * 60)
        print("✅ CAMPAIGN COMPLETE")
        print("=" * 60)
        print(json.dumps(results, indent=2))

        return results

    async def _scrape_prospects(self, niche: str, max_results: int) -> List[Prospect]:
        """Scrape prospects from web."""
        raw_prospects = self.scraper.scrape_ecommerce_leads(niche, max_results)

        # Convert to Prospect objects
        prospects = []
        for rp in raw_prospects:
            prospect = Prospect(
                name=rp.name,
                email=rp.email,
                company=rp.company,
                website=rp.website,
                platform=rp.platform,
                niche=rp.niche,
                estimated_orders=rp.estimated_orders,
                social_links=rp.social_links,
                notes=rp.notes
            )
            prospects.append(prospect)

        return prospects

    async def _enrich_prospects(self, prospects: List[Prospect]) -> List[Prospect]:
        """Enrich prospect data with additional research."""
        # Could add LinkedIn scraping, social media analysis, etc.
        # For now, just estimate pain points based on size
        enriched = []
        for p in prospects:
            pain_points = []

            if p.estimated_orders == "100-500":
                pain_points = ["overwhelmed by support tickets", "struggling to scale CS"]
            elif p.estimated_orders == "500-1000":
                pain_points = ["high cart abandonment", "missing after-hours sales"]
            elif p.estimated_orders == "1000+":
                pain_points = ["expensive CS team", "need automation"]

            p.pain_points = pain_points
            enriched.append(p)

        return enriched

    async def _generate_emails(
        self,
        prospects: List[Prospect],
        angle: Optional[str]
    ) -> List[PersonalizedEmail]:
        """Generate personalized emails for all prospects."""
        emails = []

        for i, prospect in enumerate(prospects):
            print(f"   Generating email {i+1}/{len(prospects)}: {prospect.company}...", end=" ")

            email = await self.personalizer.generate_email(
                prospect,
                tone="professional",
                custom_hook=angle
            )

            emails.append(email)
            print(f"✓ (angle: {email.angle})")

        return emails

    async def _preview_campaign(
        self,
        campaign: EmailCampaign,
        emails: List[PersonalizedEmail],
        prospects: List[Prospect]
    ) -> Dict:
        """Preview campaign without sending."""
        preview_file = self.data_dir / f"preview_{campaign.id}.txt"

        lines = [
            f"CAMPAIGN PREVIEW: {campaign.name}",
            f"Generated: {datetime.now().isoformat()}",
            f"Prospects: {len(prospects)}",
            "=" * 60,
            ""
        ]

        for i, (email, prospect) in enumerate(zip(emails, prospects)):
            lines.extend([
                f"\n--- EMAIL {i+1} ---",
                f"To: {prospect.name} <{prospect.email}>",
                f"Company: {prospect.company}",
                f"Angle: {email.angle}",
                f"Tokens: {email.tokens_used}",
                "",
                f"Subject: {email.subject}",
                "",
                "Body:",
                email.body,
                "",
                "-" * 60
            ])

        content = "\n".join(lines)

        with open(preview_file, "w") as f:
            f.write(content)

        return {
            "mode": "preview",
            "prospects": len(prospects),
            "preview_file": str(preview_file),
            "sample_subjects": [e.subject for e in emails[:3]],
            "total_tokens": sum(e.tokens_used for e in emails),
            "angles_used": list(set(e.angle for e in emails))
        }

    def get_dashboard(self) -> Dict:
        """Get outreach dashboard stats."""
        # Recent emails
        recent = self.sender.list_recent_emails(20)

        # Daily stats
        daily = self.sender.get_daily_stats()

        # Performance by angle (would connect to real data)
        angles = self.personalizer.get_template_performance()

        return {
            "daily": daily,
            "recent_emails": recent,
            "angles": angles,
            "top_performing_angles": sorted(
                angles.items(),
                key=lambda x: x[1].get("replies", 0),
                reverse=True
            )
        }


from datetime import datetime


# Test
def main():
    """Test outreach manager."""
    manager = OutreachManager()

    # Print menu
    print("\n" + "=" * 60)
    print("STUDEX AI EMAIL OUTREACH SYSTEM")
    print("=" * 60)
    print("\nOptions:")
    print("1. Run Test Campaign (preview)")
    print("2. Run Live Campaign (sends emails)")
    print("3. View Dashboard")
    print("4. Exit")

    choice = input("\nChoose option [1]: ").strip() or "1"

    if choice == "1":
        niche = input("Enter niche [fashion]: ").strip() or "fashion"
        max_p = input("Max prospects [5]: ").strip() or "5"

        results = asyncio.run(manager.run_campaign(
            niche=niche,
            max_prospects=int(max_p),
            test_mode=True
        ))

        print("\n📝 Preview saved. Check:")
        if "preview_file" in results:
            print(f"   {results['preview_file']}")

    elif choice == "2":
        print("\n⚠️  LIVE MODE - Will send real emails!")
        confirm = input("Type 'YES' to confirm: ").strip()

        if confirm == "YES":
            niche = input("Enter niche: ").strip()
            max_p = input("Max prospects [10]: ").strip() or "10"

            results = asyncio.run(manager.run_campaign(
                niche=niche,
                max_prospects=int(max_p),
                test_mode=False
            ))
        else:
            print("Cancelled.")

    elif choice == "3":
        dashboard = manager.get_dashboard()
        print("\n" + "=" * 60)
        print("OUTREACH DASHBOARD")
        print("=" * 60)
        print(f"\nDaily Stats:")
        print(f"  Sent: {dashboard['daily']['sent_today']}/{dashboard['daily']['limit']}")
        print(f"  Opened: {dashboard['daily']['opened_today']}")
        print(f"  Replied: {dashboard['daily']['replied_today']}")
        print(f"\nRecent Activity:")
        for email in dashboard['recent_emails'][:5]:
            print(f"  → {email['prospect_email']} ({email['status']})")


if __name__ == "__main__":
    main()
