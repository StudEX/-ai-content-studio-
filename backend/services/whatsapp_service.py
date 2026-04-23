"""WhatsApp Business API Service — customer messaging for SA e-commerce.

Handles:
- Incoming messages from customers
- Automated responses via Claude AI
- Order status lookups
- FAQ handling
- Human escalation
"""

import os
import httpx
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List

SAST = timezone(timedelta(hours=2))


class WhatsAppService:
    """WhatsApp Business Cloud API integration."""

    def __init__(self):
        self.phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
        self.access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
        self.business_account_id = os.getenv("WHATSAPP_BUSINESS_ACCOUNT_ID")
        self.webhook_verify_token = os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN", "studex_verify_2026")

        self.base_url = "https://graph.facebook.com/v18.0"

    @property
    def configured(self) -> bool:
        return bool(self.phone_number_id and self.access_token)

    async def send_message(
        self,
        to: str,
        message: str,
        message_type: str = "text"
    ) -> Dict:
        """Send a WhatsApp message to a customer.

        Args:
            to: Recipient phone number (with country code, e.g., +27123456789)
            message: Message content
            message_type: 'text', 'template', or 'interactive'

        Returns:
            dict: API response with message_id or error
        """
        if not self.configured:
            return {"error": "WhatsApp not configured — check env vars"}

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                payload = {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": to,
                    "type": message_type,
                }

                if message_type == "text":
                    payload["text"] = {"body": message}
                elif message_type == "template":
                    # Template messages for notifications
                    payload["template"] = message  # Caller provides full template struct
                elif message_type == "interactive":
                    # Interactive buttons/lists
                    payload["interactive"] = message

                resp = await client.post(
                    f"{self.base_url}/{self.phone_number_id}/messages",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )

                return resp.json()

            except httpx.HTTPError as e:
                return {"error": f"WhatsApp API error: {e.response.status_code if hasattr(e, 'response') else str(e)}"}
            except Exception as e:
                return {"error": str(e)}

    async def send_quick_reply(
        self,
        to: str,
        header: str,
        body: str,
        footer: str,
        buttons: List[Dict[str, str]]
    ) -> Dict:
        """Send an interactive message with quick reply buttons.

        Args:
            to: Recipient phone number
            header: Header text (max 60 chars)
            body: Main message body (max 1024 chars)
            footer: Footer text (max 60 chars)
            buttons: List of {id: str, title: str} (max 3 buttons)

        Example:
            await whatsapp.send_quick_reply(
                to="+27123456789",
                header="Order Status",
                body="What would you like to check?",
                footer="StudEx AI Assistant",
                buttons=[
                    {"id": "check_order", "title": "Check Order"},
                    {"id": "returns", "title": "Returns"},
                    {"id": "speak_human", "title": "Speak to Human"},
                ]
            )
        """
        if not self.configured:
            return {"error": "WhatsApp not configured"}

        interactive = {
            "type": "button",
            "body": {"text": body},
            "footer": {"text": footer},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": btn}
                    for btn in buttons
                ]
            }
        }

        if header:
            interactive["header"] = {"type": "text", "text": header}

        return await self.send_message(to, interactive, message_type="interactive")

    async def handle_webhook(self, payload: Dict) -> Optional[Dict]:
        """Process incoming WhatsApp webhook.

        Args:
            payload: Webhook payload from Meta

        Returns:
            dict: Response to send back, or None if no action needed
        """
        try:
            # Verify this is a message event
            if payload.get("object") != "whatsapp_business_account":
                return None

            entry = payload.get("entry", [{}])[0]
            changes = entry.get("changes", [{}])[0]
            value = changes.get("value", {})

            if value.get("messaging_product") != "whatsapp":
                return None

            # Get the message
            messages = value.get("messages", [])
            if not messages:
                return None

            message = messages[0]
            from_number = message.get("from")
            message_type = message.get("type")
            message_id = message.get("id")

            # Extract message content
            if message_type == "text":
                text = message.get("text", {}).get("body", "")
            elif message_type == "button":
                text = message.get("button", {}).get("text", "")
            elif message_type == "interactive":
                text = message.get("interactive", {}).get("button_reply", {}).get("id", "")
            else:
                text = ""

            return {
                "from": from_number,
                "text": text,
                "message_type": message_type,
                "message_id": message_id,
                "timestamp": datetime.now(SAST).isoformat(),
            }

        except Exception as e:
            return {"error": f"Webhook processing failed: {str(e)}"}

    async def verify_webhook(self, mode: str, token: str, challenge: str) -> str:
        """Verify webhook subscription challenge from Meta.

        Returns:
            str: Challenge string if verified, empty string otherwise
        """
        if mode == "subscribe" and token == self.webhook_verify_token:
            return challenge
        return ""

    async def get_profile(self, phone_number: str) -> Dict:
        """Get WhatsApp profile info for a phone number."""
        if not self.configured:
            return {"error": "WhatsApp not configured"}

        async with httpx.AsyncClient(timeout=10) as client:
            try:
                resp = await client.get(
                    f"{self.base_url}/{self.phone_number_id}",
                    params={"fields": "name,about"},
                    headers={"Authorization": f"Bearer {self.access_token}"}
                )
                return resp.json()
            except Exception as e:
                return {"error": str(e)}


# Customer service agent integration
class CustomerServiceAgent:
    """AI-powered customer service agent for e-commerce.

    Handles:
    - Order status inquiries
    - Returns and exchanges
    - Product FAQs
    - Shipping questions
    - Escalation to human agents
    """

    def __init__(self, whatsapp: WhatsAppService, store_config: Dict):
        self.whatsapp = whatsapp
        self.store_config = store_config  # Store-specific settings
        self.conversation_history: Dict[str, List[Dict]] = {}  # Per-customer history

    async def handle_customer_message(
        self,
        customer_phone: str,
        message: str,
        order_db: Optional[Dict] = None
    ) -> str:
        """Process customer message and generate AI response.

        Args:
            customer_phone: Customer's WhatsApp number
            message: Incoming message text
            order_db: Optional order database lookup function

        Returns:
            str: Response message to send back
        """
        from services.claude_service import ClaudeService

        claude = ClaudeService()
        if not claude.configured:
            return "Thank you for your message. We'll get back to you shortly."

        # Build conversation context
        history = self.conversation_history.get(customer_phone, [])
        history.append({"role": "user", "content": message})

        # System prompt for customer service
        system_prompt = f"""You are a friendly customer service assistant for {self.store_config.get('store_name', 'our store')}.

Your role:
- Help customers check order status
- Answer questions about products, shipping, returns
- Be warm, helpful, and concise (WhatsApp messages should be short)
- If you don't know something, offer to connect them with a human
- All prices in ZAR (South African Rand)
- Shipping is within South Africa only

Store policies:
- Returns: {self.store_config.get('returns_policy', '30 days, unused items')}
- Shipping: {self.store_config.get('shipping_policy', '2-5 business days, R99 flat rate')}
- Payment: {self.store_config.get('payment_methods', 'Card, EFT, Cash on Delivery')}

Keep responses under 160 characters when possible (one WhatsApp message).
Be friendly and use emojis sparingly. 🛍️"""

        # Build prompt with order context if available
        order_context = ""
        if order_db:
            # Look up customer's recent orders
            orders = order_db.get(customer_phone, [])
            if orders:
                order_context = f"\n\nCustomer's recent orders:\n{orders}"

        prompt = f"Customer message: {message}{order_context}\n\nGenerate a helpful response:"

        # Generate response
        response, usage = await claude.generate(
            system=system_prompt,
            prompt=prompt,
            model="claude-haiku-4-5",  # Fast, cheap for simple queries
            max_tokens=200,
            use_thinking=False,
            effort="low",
        )

        # Update history
        history.append({"role": "assistant", "content": response})
        self.conversation_history[customer_phone] = history[-10:]  # Keep last 10

        return response

    async def check_order_status(self, customer_phone: str, order_id: str) -> str:
        """Check order status for a customer.

        This would integrate with the store's order management system.
        For MVP, returns a template response.
        """
        # TODO: Integrate with store's order DB
        return f"Let me check order #{order_id} for you... One moment! 📦"

    async def initiate_return(self, customer_phone: str, order_id: str) -> str:
        """Start a return/exchange process."""
        return f"I can help you return order #{order_id}. Was the item damaged, or would you like a different size/color?"

    async def escalate_to_human(self, customer_phone: str, context: str) -> bool:
        """Escalate conversation to human agent.

        Returns:
            bool: True if escalation successful
        """
        # TODO: Send notification to human agent (Slack, email, SMS)
        print(f"ESCALATION: Customer {customer_phone} needs human help. Context: {context}")
        return True
