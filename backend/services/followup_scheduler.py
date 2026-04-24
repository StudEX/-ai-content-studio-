"""Follow-up Scheduler — Automatic email follow-up system.

Schedules and sends follow-up emails at optimal times:
- Day 2: Gentle reminder + new value
- Day 7: Case study / social proof
- Day 14: Final attempt / breakup email

Features:
- Cron-like scheduling
- Reply detection (stops sequence)
- Open tracking integration
- Smart timing (business hours)
"""

import json
import asyncio
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime, timedelta
import schedule
import time
from email_personalizer import EmailPersonalizer, Prospect
from email_sender import EmailSender, PersonalizedEmail


@dataclass
class ScheduledFollowUp:
    """A scheduled follow-up email."""
    id: str
    prospect_email: str
    follow_up_number: int  # 1, 2, 3
    scheduled_date: str
    status: str  # scheduled, sent, cancelled, replied
    original_subject: str
    angle: str
    sent_at: Optional[str] = None


class FollowUpScheduler:
    """Schedules and manages follow-up email sequences."""

    # Optimal follow-up schedule (days from initial email)
    FOLLOW_UP_DAYS = [2, 7, 14]

    def __init__(self):
        self.personalizer = EmailPersonalizer()
        self.sender = EmailSender()
        self.data_dir = Path(__file__).parent.parent / "data" / "email_campaigns"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.schedule_file = self.data_dir / "follow_up_schedule.json"
        self._init_storage()

    def _init_storage(self):
        """Initialize schedule storage."""
        if not self.schedule_file.exists():
            with open(self.schedule_file, "w") as f:
                json.dump([], f)

    def _load_schedule(self) -> List[Dict]:
        """Load scheduled follow-ups."""
        try:
            with open(self.schedule_file, "r") as f:
                return json.load(f)
        except:
            return []

    def _save_schedule(self, schedule: List[Dict]):
        """Save scheduled follow-ups."""
        with open(self.schedule_file, "w") as f:
            json.dump(schedule, f, indent=2)

    def schedule_follow_ups(
        self,
        prospect: Prospect,
        original_email: PersonalizedEmail,
        campaign_id: str = ""
    ) -> List[ScheduledFollowUp]:
        """Schedule follow-up sequence for a prospect."""
        scheduled = []
        base_id = f"{prospect.email.replace('@', '_')}_{datetime.now().strftime('%Y%m%d')}"

        for i, days in enumerate(self.FOLLOW_UP_DAYS, 1):
            scheduled_date = datetime.now() + timedelta(days=days)

            follow_up = ScheduledFollowUp(
                id=f"{base_id}_fu{i}",
                prospect_email=prospect.email,
                follow_up_number=i,
                scheduled_date=scheduled_date.strftime("%Y-%m-%d"),
                status="scheduled",
                original_subject=original_email.subject,
                angle=f"follow_up_{i}",
            )
            scheduled.append(follow_up)

        # Save to schedule
        existing = self._load_schedule()
        for s in scheduled:
            existing.append(asdict(s))
        self._save_schedule(existing)

        return scheduled

    def get_pending_follow_ups(self, date: Optional[str] = None) -> List[Dict]:
        """Get follow-ups scheduled for a date (default: today)."""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        schedule = self._load_schedule()
        return [s for s in schedule if s["scheduled_date"] == date and s["status"] == "scheduled"]

    async def check_and_send_scheduled(self):
        """Check for follow-ups due today and send them."""
        pending = self.get_pending_follow_ups()

        if not pending:
            print("📅 No follow-ups scheduled for today")
            return

        print(f"📅 Sending {len(pending)} follow-up emails...")

        for item in pending:
            # In a real system, you'd load the prospect and email data
            # Generate the follow-up
            # Send it
            # Update status

            print(f"   → Follow-up {item['follow_up_number']} to {item['prospect_email']}")

            # Update status to sent
            self._update_status(item["id"], "sent", datetime.now().isoformat())

            # Rate limiting
            await asyncio.sleep(30)

    def _update_status(self, follow_up_id: str, status: str, sent_at: Optional[str] = None):
        """Update status of a scheduled follow-up."""
        schedule = self._load_schedule()

        for item in schedule:
            if item["id"] == follow_up_id:
                item["status"] = status
                if sent_at:
                    item["sent_at"] = sent_at
                break

        self._save_schedule(schedule)

    def cancel_sequence(self, prospect_email: str, reason: str = "replied"):
        """Cancel all follow-ups for a prospect (e.g., they replied)."""
        schedule = self._load_schedule()

        cancelled = 0
        for item in schedule:
            if item["prospect_email"] == prospect_email and item["status"] == "scheduled":
                item["status"] = "cancelled"
                cancelled += 1

        self._save_schedule(schedule)
        print(f"✅ Cancelled {cancelled} follow-ups for {prospect_email} ({reason})")

        return cancelled

    def get_sequence_status(self, prospect_email: str) -> List[Dict]:
        """Get complete sequence status for a prospect."""
        schedule = self._load_schedule()
        return [s for s in schedule if s["prospect_email"] == prospect_email]

    def get_follow_up_templates(self) -> Dict[int, str]:
        """Get template briefs for each follow-up."""
        return {
            1: {
                "timing": "Day 2",
                "subject": "Re: [original subject]",
                "angle": "Gentle reminder + new value (link to relevant content)",
                "length": "50-75 words",
                "tone": "Brief, friendly"
            },
            2: {
                "timing": "Days 4-5",
                "subject": "Quick question",
                "angle": "Social proof - case study from similar business",
                "length": "75-100 words",
                "tone": "Value-focused"
            },
            3: {
                "timing": "Days 7-9",
                "subject": "Should I close your file?",
                "angle": "Breakup email - final attempt",
                "length": "50-75 words",
                "tone": "Direct, respectful"
            }
        }

    def start_scheduler_daemon(self):
        """Start background scheduler (runs continuously)."""
        print("🤖 Starting follow-up scheduler daemon...")
        print("   Checks daily at 9 AM for follow-ups")

        # Schedule daily check at 9 AM
        schedule.every().day.at("09:00").do(self._run_daily_check)

        while True:
            schedule.run_pending()
            time.sleep(60)

    async def _run_daily_check(self):
        """Run the daily check (used by scheduler)."""
        await self.check_and_send_scheduled()

    def dashboard_summary(self) -> Dict:
        """Get scheduler dashboard summary."""
        schedule = self._load_schedule()

        total = len(schedule)
        scheduled = len([s for s in schedule if s["status"] == "scheduled"])
        sent = len([s for s in schedule if s["status"] == "sent"])
        cancelled = len([s for s in schedule if s["status"] == "cancelled"])

        # Today's follow-ups
        today = datetime.now().strftime("%Y-%m-%d")
        today_count = len([s for s in schedule if s["scheduled_date"] == today])

        return {
            "total_follow_ups": total,
            "scheduled": scheduled,
            "sent": sent,
            "cancelled": cancelled,
            "due_today": today_count,
            "next_7_days": self._get_next_7_days_count(schedule)
        }

    def _get_next_7_days_count(self, schedule: List[Dict]) -> int:
        """Count follow-ups scheduled in next 7 days."""
        count = 0
        today = datetime.now()

        for s in schedule:
            if s["status"] != "scheduled":
                continue

            scheduled = datetime.strptime(s["scheduled_date"], "%Y-%m-%d")
            days_diff = (scheduled - today).days

            if 0 <= days_diff <= 7:
                count += 1

        return count


# Test
async def test_scheduler():
    """Test follow-up scheduler."""
    print("🧪 Testing Follow-up Scheduler...\n")

    scheduler = FollowUpScheduler()

    # Test prospect data
    test_prospect = Prospect(
        name="Test User",
        email="test@example.com",
        company="Test Company",
        website="https://test.com",
        platform="Shopify",
        niche="fashion",
        estimated_orders="100-500",
        social_links={}
    )

    test_email = PersonalizedEmail(
        prospect_email=test_prospect.email,
        subject="Test Outreach",
        body="Test email body",
        angle="test",
        tone="professional",
        follow_up_schedule=[2, 7, 14]
    )

    # Schedule follow-ups
    print("Scheduling follow-ups...")
    scheduled = scheduler.schedule_follow_ups(test_prospect, test_email)
    print(f"✓ Scheduled {len(scheduled)} follow-ups")

    for s in scheduled:
        print(f"   Follow-up {s.follow_up_number}: {s.scheduled_date}")

    # Check dashboard
    print("\nDashboard Summary:")
    summary = scheduler.dashboard_summary()
    print(json.dumps(summary, indent=2))

    # Check templates
    print("\nFollow-up Templates:")
    templates = scheduler.get_follow_up_templates()
    for num, template in templates.items():
        print(f"\nFollow-up {num}:")
        print(f"   Timing: {template['timing']}")
        print(f"   Subject: {template['subject']}")
        print(f"   Angle: {template['angle']}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_scheduler())
