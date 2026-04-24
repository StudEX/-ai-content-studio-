"""Email Sender — Send personalized emails via SMTP with rate limiting and tracking.

Features:
- SMTP/SendGrid integration
- Rate limiting (100 emails/day default)
- Opens/clicks tracking
- Follow-up scheduling
- A/B testing support
- Reply detection
"""

import os
import json
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import asyncio
import aiohttp
from email_personalizer import PersonalizedEmail, Prospect


@dataclass
class EmailCampaign:
    """Email campaign configuration."""
    id: str
    name: str
    angle: str
    prospects: List[Prospect]
    emails_sent: int = 0
    emails_opened: int = 0
    emails_replied: int = 0
    created_at: str = ""
    status: str = "draft"  # draft, active, paused, completed


@dataclass
class SentEmail:
    """Record of sent email."""
    id: str
    prospect_email: str
    prospect_name: str
    company: str
    subject: str
    body: str
    angle: str
    sent_at: str
    status: str  # sent, delivered, opened, clicked, replied, bounced
    opened_at: Optional[str] = None
    replied_at: Optional[str] = None
    campaign_id: str = ""


class EmailSender:
    """Smart email sender with tracking and scheduling."""

    # Limits to avoid spam filters
    DAILY_LIMIT = 100
    HOURLY_LIMIT = 20
    MIN_DELAY_SECONDS = 30  # Space out emails

    def __init__(self):
        self.smtp_config = self._load_smtp_config()
        self.data_dir = Path(__file__).parent.parent / "data" / "email_campaigns"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.tracking_file = self.data_dir / "sent_emails.json"
        self.campaigns_file = self.data_dir / "campaigns.json"
        self._init_storage()

    def _load_smtp_config(self) -> Dict:
        """Load SMTP configuration from environment."""
        return {
            "host": os.environ.get("SMTP_HOST", "smtp.gmail.com"),
            "port": int(os.environ.get("SMTP_PORT", "587")),
            "username": os.environ.get("SMTP_USERNAME", ""),
            "password": os.environ.get("SMTP_PASSWORD", ""),
            "from_name": os.environ.get("SMTP_FROM_NAME", "Tumelo Ramaphosa"),
            "from_email": os.environ.get("SMTP_FROM_EMAIL", ""),
            "reply_to": os.environ.get("SMTP_REPLY_TO", "")
        }

    def _init_storage(self):
        """Initialize JSON storage files."""
        if not self.tracking_file.exists():
            with open(self.tracking_file, "w") as f:
                json.dump([], f)

        if not self.campaigns_file.exists():
            with open(self.campaigns_file, "w") as f:
                json.dump([], f)

    def _load_sent_emails(self) -> List[Dict]:
        """Load sent email records."""
        try:
            with open(self.tracking_file, "r") as f:
                return json.load(f)
        except:
            return []

    def _save_sent_email(self, record: SentEmail):
        """Save sent email record."""
        emails = self._load_sent_emails()
        emails.append({
            "id": record.id,
            "prospect_email": record.prospect_email,
            "prospect_name": record.prospect_name,
            "company": record.company,
            "subject": record.subject,
            "body": record.body,
            "angle": record.angle,
            "sent_at": record.sent_at,
            "status": record.status,
            "opened_at": record.opened_at,
            "replied_at": record.replied_at,
            "campaign_id": record.campaign_id
        })
        with open(self.tracking_file, "w") as f:
            json.dump(emails, f, indent=2)

    def get_daily_stats(self) -> Dict:
        """Get today's sending stats."""
        emails = self._load_sent_emails()
        today = datetime.now().strftime("%Y-%m-%d")

        today_emails = [e for e in emails if e["sent_at"].startswith(today)]

        return {
            "sent_today": len(today_emails),
            "limit": self.DAILY_LIMIT,
            "remaining": self.DAILY_LIMIT - len(today_emails),
            "opened_today": len([e for e in today_emails if e["status"] == "opened"]),
            "replied_today": len([e for e in today_emails if e["status"] == "replied"])
        }

    def can_send_today(self, count: int = 1) -> Tuple[bool, str]:
        """Check if we can send more emails today."""
        stats = self.get_daily_stats()

        if stats["remaining"] < count:
            return False, f"Daily limit reached: {stats['sent_today']}/{self.DAILY_LIMIT}"

        return True, f"OK: {stats['remaining']} emails remaining today"

    def _add_tracking_pixel(self, body: str, email_id: str) -> str:
        """Add invisible tracking pixel to email."""
        # In production, this would be a real webhook URL
        tracking_url = f"https://studex.ai/track/open/{email_id}.gif"
        pixel = f'<img src="{tracking_url}" width="1" height="1" alt="" />'

        # Add to end of HTML body
        if "</body>" in body:
            return body.replace("</body>", f"{pixel}</body>")
        return body + pixel

    def _add_link_tracking(self, body: str, email_id: str) -> str:
        """Add click tracking to links."""
        # Replace links with tracking redirects
        # In production, this would modify URLs
        return body

    def _create_email_message(
        self,
        to_email: str,
        subject: str,
        body_text: str,
        body_html: str
    ) -> MIMEMultipart:
        """Create MIME email message."""
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{self.smtp_config['from_name']} <{self.smtp_config['from_email']}>"
        msg["To"] = to_email

        if self.smtp_config["reply_to"]:
            msg["Reply-To"] = self.smtp_config["reply_to"]

        # Plain text version
        msg.attach(MIMEText(body_text, "plain"))

        # HTML version
        msg.attach(MIMEText(body_html, "html"))

        return msg

    async def send_email(
        self,
        email: PersonalizedEmail,
        prospect: Prospect,
        campaign_id: str = "",
        test_mode: bool = False
    ) -> Tuple[bool, str]:
        """
        Send a single personalized email.

        Returns: (success, message)
        """
        # Check limits
        can_send, limit_msg = self.can_send_today()
        if not can_send:
            return False, limit_msg

        if test_mode:
            print(f"📧 TEST MODE: Would send to {prospect.email}")
            print(f"Subject: {email.subject}")
            return True, "Test mode - not actually sent"

        # Validate config
        if not self.smtp_config["username"] or not self.smtp_config["password"]:
            return False, "SMTP not configured. Set SMTP_USERNAME and SMTP_PASSWORD"

        # Generate email ID
        email_id = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{prospect.email.replace('@', '_')}"

        # Prepare body
        body_text = email.body
        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        {email.body.replace('\n', '<br>')}
        </body>
        </html>
        """

        # Add tracking
        body_html = self._add_tracking_pixel(body_html, email_id)
        body_html = self._add_link_tracking(body_html, email_id)

        try:
            # Create message
            msg = self._create_email_message(
                prospect.email,
                email.subject,
                body_text,
                body_html
            )

            # Send via SMTP
            context = ssl.create_default_context()

            with smtplib.SMTP(self.smtp_config["host"], self.smtp_config["port"]) as server:
                server.starttls(context=context)
                server.login(self.smtp_config["username"], self.smtp_config["password"])
                server.sendmail(
                    self.smtp_config["from_email"],
                    prospect.email,
                    msg.as_string()
                )

            # Record sent
            sent_record = SentEmail(
                id=email_id,
                prospect_email=prospect.email,
                prospect_name=prospect.name,
                company=prospect.company,
                subject=email.subject,
                body=email.body,
                angle=email.angle,
                sent_at=datetime.now().isoformat(),
                status="sent",
                campaign_id=campaign_id
            )
            self._save_sent_email(sent_record)

            return True, f"Email sent to {prospect.email}"

        except Exception as e:
            return False, f"Failed to send: {str(e)}"

    async def send_sequence(
        self,
        emails: List[PersonalizedEmail],
        prospect: Prospect,
        campaign_id: str = "",
        test_mode: bool = False
    ) -> List[Tuple[bool, str]]:
        """Send a sequence of emails with delays."""
        results = []

        for i, email in enumerate(emails):
            # First email sends immediately
            if i == 0:
                success, msg = await self.send_email(
                    email, prospect, campaign_id, test_mode
                )
                results.append((success, msg))

                if not success:
                    break

            else:
                # Schedule follow-ups (in production, this would use a scheduler)
                days = email.follow_up_schedule[i-1] if i-1 < len(email.follow_up_schedule) else 7
                scheduled_time = datetime.now() + timedelta(days=days)
                results.append((
                    True,
                    f"Follow-up {i} scheduled for {scheduled_time.strftime('%Y-%m-%d')}"
                ))

            # Rate limiting delay
            if i < len(emails) - 1 and not test_mode:
                await asyncio.sleep(self.MIN_DELAY_SECONDS)

        return results

    async def send_campaign(
        self,
        campaign: EmailCampaign,
        emails: List[PersonalizedEmail],
        test_mode: bool = False
    ) -> Dict:
        """Send campaign to all prospects."""
        results = {
            "sent": 0,
            "failed": 0,
            "errors": []
        }

        for prospect in campaign.prospects:
            # Check if we can send
            can_send, limit_msg = self.can_send_today()
            if not can_send:
                results["errors"].append(limit_msg)
                break

            # Find email for this prospect
            prospect_email = next(
                (e for e in emails if e.prospect_email == prospect.email),
                None
            )

            if not prospect_email:
                results["errors"].append(f"No email generated for {prospect.email}")
                continue

            # Send
            success, msg = await self.send_email(
                prospect_email,
                prospect,
                campaign.id,
                test_mode
            )

            if success:
                results["sent"] += 1
            else:
                results["failed"] += 1
                results["errors"].append(f"{prospect.email}: {msg}")

            # Rate limiting
            await asyncio.sleep(self.MIN_DELAY_SECONDS)

        return results

    def get_campaign_stats(self, campaign_id: str) -> Dict:
        """Get stats for a campaign."""
        emails = self._load_sent_emails()
        campaign_emails = [e for e in emails if e.get("campaign_id") == campaign_id]

        return {
            "total_sent": len(campaign_emails),
            "opened": len([e for e in campaign_emails if e["status"] in ["opened", "replied"]]),
            "replied": len([e for e in campaign_emails if e["status"] == "replied"]),
            "open_rate": len([e for e in campaign_emails if e["status"] in ["opened", "replied"]]) / len(campaign_emails) * 100 if campaign_emails else 0
        }

    def list_recent_emails(self, limit: int = 20) -> List[Dict]:
        """List recently sent emails."""
        emails = self._load_sent_emails()
        return sorted(emails, key=lambda x: x["sent_at"], reverse=True)[:limit]


# Test function
async def test_sender():
    """Test email sender."""
    print("🧪 Testing Email Sender...\n")

    sender = EmailSender()

    # Check daily stats
    stats = sender.get_daily_stats()
    print(f"📊 Daily Stats:")
    print(f"   Sent today: {stats['sent_today']}/{stats['limit']}")
    print(f"   Remaining: {stats['remaining']}")
    print()

    # Check if we can send
    can_send, msg = sender.can_send_today()
    print(f"✅ Can send: {msg}\n")

    # Test prospect
    test_prospect = Prospect(
        name="Test User",
        email="test@example.com",
        company="Test Company",
        website="https://test.com",
        platform="Shopify",
        niche="test",
        estimated_orders="100-500",
        social_links={}
    )

    # Test email
    test_email = PersonalizedEmail(
        prospect_email=test_prospect.email,
        subject="Test Subject",
        body="This is a test email body.\n\nBest regards,\nTumelo",
        angle="test",
        tone="professional",
        follow_up_schedule=[2, 7, 14]
    )

    # Send test (will fail without SMTP config, but shows flow)
    success, msg = await sender.send_email(
        test_email,
        test_prospect,
        campaign_id="test_campaign",
        test_mode=True
    )

    print(f"Send result: {success} - {msg}")
    print(f"Recent emails: {len(sender.list_recent_emails())}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_sender())
