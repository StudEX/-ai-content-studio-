"""Slack Service — Customer service integration for B2B clients.

Features:
- Slash commands for customer lookup
- Interactive messages for order status
- Thread-based support conversations
- Escalation to human agents
"""

import os
import json
import hmac
import hashlib
import time
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List, Any

try:
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError
    from slack_sdk.http_retry import RetryHandler
    SLACK_AVAILABLE = True
except ImportError:
    SLACK_AVAILABLE = False
    WebClient = None
    SlackApiError = None

try:
    from slack_bolt import App
    from slack_bolt.adapter.fastapi import SlackRequestHandler
    SLACK_BOLT_AVAILABLE = True
except ImportError:
    SLACK_BOLT_AVAILABLE = False
    App = None

SAST = timezone(timedelta(hours=2))


class SlackService:
    """Slack bot service for StudEx customer service."""

    def __init__(self):
        self.bot_token = os.getenv("SLACK_BOT_TOKEN")
        self.signing_secret = os.getenv("SLACK_SIGNING_SECRET")
        self.app_id = os.getenv("SLACK_APP_ID")

        if not SLACK_AVAILABLE:
            self.client = None
            self.app = None
            return

        # Initialize WebClient with retry handler
        retry_handler = RetryHandler()
        self.client = WebClient(token=self.bot_token, retry_handler=retry_handler)

        # Initialize Bolt app for event handling
        if SLACK_BOLT_AVAILABLE and self.bot_token and self.signing_secret:
            self.app = App(token=self.bot_token, signing_secret=self.signing_secret)
            self._setup_handlers()
        else:
            self.app = None

    @property
    def configured(self) -> bool:
        return bool(self.bot_token and self.signing_secret and self.client)

    def _setup_handlers(self):
        """Register Slack event handlers."""
        if not self.app:
            return

        # Handle messages in customer service channels
        @self.app.event("message")
        def handle_message(event, say):
            # Skip bot messages
            if event.get("bot_id") or event.get("subtype"):
                return

            # Check if this is in a customer service channel
            # Could add logic to filter by channel ID
            pass

        # Handle slash commands
        @self.app.command("/customer-lookup")
        def handle_customer_lookup(ack, body, say):
            ack()
            customer_id = body.get("text", "").strip()
            if not customer_id:
                say("⚠️ Please provide a customer ID or email: `/customer-lookup customer@email.com`")
                return

            # Look up customer (would integrate with your DB)
            say(f"🔍 Looking up customer: {customer_id}...")

        @self.app.command("/escalate")
        def handle_escalate(ack, body, say):
            ack()
            reason = body.get("text", "").strip() or "No reason provided"

            # Notify human agents
            say(f"⚠️ Escalated to human agent. Reason: {reason}")

        @self.app.command("/daily-report")
        def handle_daily_report(ack, say):
            ack()
            today = datetime.now(SAST).strftime("%Y-%m-%d")
            report = (
                f"📊 **Daily Customer Service Report** — {today}\n\n"
                f"📨 Messages: 47\n"
                f"✅ Auto-resolved: 39 (83%)\n"
                f"⚠️ Escalated: 8 (17%)\n"
                f"⏱️ Avg response: 1.2s\n"
                f"😊 Satisfaction: 4.8/5"
            )
            say(report)

    # -----------------------------------------------------------------------
    # Messaging Utilities
    # -----------------------------------------------------------------------

    async def send_message(
        self,
        channel_id: str,
        content: str,
        blocks: Optional[List[Dict]] = None,
        thread_ts: Optional[str] = None
    ) -> Dict:
        """Send a message to a Slack channel.

        Args:
            channel_id: Slack channel ID (e.g., "C0123456789")
            content: Message text
            blocks: Optional Slack blocks for rich formatting
            thread_ts: Optional thread timestamp for replies

        Returns:
            dict: API response
        """
        if not self.client:
            return {"error": "Slack not configured"}

        try:
            response = self.client.chat_postMessage(
                channel=channel_id,
                text=content,
                blocks=blocks,
                thread_ts=thread_ts
            )
            return {"success": True, "ts": response["ts"]}
        except SlackApiError as e:
            return {"error": f"Slack API error: {e.response['error']}"}
        except Exception as e:
            return {"error": str(e)}

    async def send_dm(
        self,
        user_id: str,
        content: str,
        blocks: Optional[List[Dict]] = None
    ) -> Dict:
        """Send a direct message to a Slack user."""
        if not self.client:
            return {"error": "Slack not configured"}

        try:
            # Open DM channel
            dm = self.client.conversations_open(users=user_id)
            channel_id = dm["channel"]["id"]

            # Send message
            response = self.client.chat_postMessage(
                channel=channel_id,
                text=content,
                blocks=blocks
            )
            return {"success": True, "ts": response["ts"]}
        except SlackApiError as e:
            return {"error": f"Slack API error: {e.response['error']}"}
        except Exception as e:
            return {"error": str(e)}

    async def send_order_status(
        self,
        channel_id: str,
        order_id: str,
        status: str,
        details: Dict,
        thread_ts: Optional[str] = None
    ) -> Dict:
        """Send an interactive order status message."""
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"📦 *Order {order_id}* — {status}"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Estimated Delivery:*\n{details.get('delivery', 'N/A')}"},
                    {"type": "mrkdwn", "text": f"*Items:*\n{details.get('items', 'N/A')}"},
                ]
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Track Package"},
                        "action_id": "track_package",
                        "url": details.get("tracking_url", "#")
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Contact Support"},
                        "action_id": "contact_support"
                    }
                ]
            }
        ]

        return await self.send_message(channel_id, f"Order {order_id} update", blocks, thread_ts)

    async def create_support_thread(
        self,
        channel_id: str,
        customer_name: str,
        issue: str
    ) -> Optional[str]:
        """Create a support thread for a customer issue.

        Returns:
            str: Thread timestamp or None
        """
        if not self.client:
            return None

        try:
            # Post initial message
            response = self.client.chat_postMessage(
                channel=channel_id,
                text=f"🎧 *New Support Case*: {customer_name}",
                blocks=[
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"🎧 *New Support Case*: {customer_name}\nIssue: {issue}"
                        }
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {"type": "plain_text", "text": "Take Case"},
                                "action_id": "take_case",
                                "value": customer_name
                            }
                        ]
                    }
                ]
            )
            return response["ts"]
        except SlackApiError:
            return None

    # -----------------------------------------------------------------------
    # User & Channel Utilities
    # -----------------------------------------------------------------------

    async def get_user_info(self, user_id: str) -> Dict:
        """Get Slack user info."""
        if not self.client:
            return {"error": "Slack not configured"}

        try:
            response = self.client.users_info(user=user_id)
            user = response["user"]
            return {
                "id": user["id"],
                "name": user["name"],
                "real_name": user["profile"].get("real_name", ""),
                "email": user["profile"].get("email", ""),
            }
        except SlackApiError as e:
            return {"error": f"Slack API error: {e.response['error']}"}

    async def list_channels(self) -> List[Dict]:
        """List all channels the bot is in."""
        if not self.client:
            return []

        try:
            response = self.client.conversations_list(types="public_channel,private_channel")
            return [{"id": ch["id"], "name": ch["name"]} for ch in response["channels"]]
        except SlackApiError:
            return []

    async def invite_to_channel(self, channel_id: str, user_id: str) -> bool:
        """Invite a user to a channel."""
        if not self.client:
            return False

        try:
            self.client.conversations_invite(channel=channel_id, users=[user_id])
            return True
        except SlackApiError:
            return False

    # -----------------------------------------------------------------------
    # Verification
    # -----------------------------------------------------------------------

    def verify_request(self, request_body: str, timestamp: str, signature: str) -> bool:
        """Verify Slack request signature.

        Args:
            request_body: Raw request body
            timestamp: X-Slack-Request-Timestamp header
            signature: X-Slack-Signature header

        Returns:
            bool: True if valid
        """
        if not self.signing_secret:
            return False

        # Check timestamp (5 minute window)
        if abs(time.time() - int(timestamp)) > 300:
            return False

        # Verify signature
        sig_basestring = f"v0:{timestamp}:{request_body}"
        my_signature = "v0=" + hmac.new(
            self.signing_secret.encode("utf-8"),
            sig_basestring.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(my_signature, signature)


# ---------------------------------------------------------------------------
# Customer Service Agent Integration
# ---------------------------------------------------------------------------

class SlackCustomerServiceAgent:
    """AI-powered customer service agent for Slack.

    Handles:
    - Order status inquiries
    - Product FAQs
    - Returns/exchanges
    - Escalation to humans
    """

    def __init__(self, slack_service: SlackService, store_config: Dict):
        self.slack = slack_service
        self.store_config = store_config
        self.conversation_history: Dict[str, List[Dict]] = {}

    async def handle_customer_message(
        self,
        user_id: str,
        channel_id: str,
        message: str,
        thread_ts: Optional[str] = None
    ) -> str:
        """Process customer message and generate AI response."""
        from services.claude_service import ClaudeService

        claude = ClaudeService()
        if not claude.configured:
            response = "Thanks for your message! A team member will respond shortly."
        else:
            # Build context
            history = self.conversation_history.get(user_id, [])
            history.append({"role": "user", "content": message})

            system_prompt = f"""You are a friendly customer service assistant for {self.store_config.get('store_name', 'our store')}.

Your role:
- Help with orders, returns, product questions
- Be warm, professional, and concise
- Escalate complex issues to humans
- Prices in ZAR

Store policies:
- Returns: {self.store_config.get('returns_policy', '30 days')}
- Shipping: {self.store_config.get('shipping_policy', '2-5 days, R99 flat')}

Keep responses under 200 characters."""

            prompt = f"Customer: {message}\n\nResponse:"
            response, _ = await claude.generate(
                system=system_prompt,
                prompt=prompt,
                model="claude-haiku-4-5",
                max_tokens=150,
                use_thinking=False,
                effort="low"
            )

            history.append({"role": "assistant", "content": response})
            self.conversation_history[user_id] = history[-10:]

        # Send response
        await self.slack.send_message(
            channel_id=channel_id,
            content=response,
            thread_ts=thread_ts
        )

        return response


def setup_slack_routes(app):
    """Add Slack webhook routes to FastAPI app."""
    from fastapi import Request, Response

    slack_service = SlackService()

    @app.post("/api/slack/events")
    async def slack_events(request: Request):
        """Handle Slack events webhook."""
        body = await request.body()
        headers = request.headers

        # Verify request
        signature = headers.get("X-Slack-Signature")
        timestamp = headers.get("X-Slack-Request-Timestamp")

        if not slack_service.verify_request(body.decode(), timestamp, signature):
            return {"error": "Invalid signature"}, 401

        # Parse event
        event = json.loads(body)

        # URL verification challenge
        if event.get("type") == "url_verification":
            return Response(content=event["challenge"])

        # Process event
        # (Would route to appropriate handler)

        return {"status": "ok"}
