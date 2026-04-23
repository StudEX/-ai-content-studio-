"""Stitch.money Payment Service — African payment processing.

Stitch provides:
- Instant EFT (South Africa)
- Card payments
- Debit orders
- Payment links

Integration via Playwright for OAuth flow + REST API for transactions.
"""

import os
import json
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List
from playwright.async_api import async_playwright

SAST = timezone(timedelta(hours=2))


class StitchService:
    """Stitch.money payment integration."""

    def __init__(self):
        self.client_id = os.getenv("STITCH_CLIENT_ID")
        self.client_secret = os.getenv("STITCH_CLIENT_SECRET")
        self.access_token = os.getenv("STITCH_ACCESS_TOKEN")
        self.environment = os.getenv("STITCH_ENV", "sandbox")  # sandbox | production

        # API endpoints
        self.base_url = (
            "https://express.stitch.money" if self.environment == "production"
            else "https://sandbox.express.stitch.money"
        )
        self.api_url = "https://api.stitch.money"

    @property
    def configured(self) -> bool:
        return bool(self.client_id and self.client_secret)

    @property
    def authenticated(self) -> bool:
        return bool(self.access_token)

    # -----------------------------------------------------------------------
    # OAuth Authentication (Playwright)
    # -----------------------------------------------------------------------

    async def authenticate_with_playwright(self, email: str, password: str) -> Dict:
        """Authenticate with Stitch using Playwright (handles OAuth flow).

        Args:
            email: Stitch account email
            password: Stitch account password

        Returns:
            dict: {success: bool, access_token: str, error: str}
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)  # Headless=False for 2FA if needed
            context = await browser.new_context()
            page = await context.new_page()

            try:
                # Go to login
                await page.goto(f"{self.base_url}/login", wait_until="networkidle")

                # Enter credentials
                await page.fill('input[type="email"]', email)
                await page.fill('input[type="password"]', password)

                # Submit
                await page.click('button[type="submit"]')
                await page.wait_for_load_state("networkidle")

                # Wait for redirect to dashboard (indicates successful login)
                await page.wait_for_url(f"{self.base_url}/dashboard*", timeout=10000)

                # Extract access token from localStorage or cookies
                access_token = await page.evaluate("""() => {
                    // Try localStorage first
                    const token = localStorage.getItem('stitch_access_token');
                    if (token) return token;

                    // Try cookies
                    const cookie = document.cookie
                        .split('; ')
                        .find(row => row.startsWith('stitch_token='));
                    return cookie ? cookie.split('=')[1] : null;
                }""")

                if access_token:
                    # Save token
                    self.access_token = access_token
                    return {
                        "success": True,
                        "access_token": access_token,
                        "message": "Successfully authenticated with Stitch"
                    }
                else:
                    return {
                        "success": False,
                        "error": "Could not extract access token. Check browser console."
                    }

            except Exception as e:
                return {
                    "success": False,
                    "error": f"Authentication failed: {str(e)}"
                }
            finally:
                await browser.close()

    async def get_oauth_url(self, redirect_uri: str) -> str:
        """Generate OAuth URL for user authorization.

        Args:
            redirect_uri: Where to redirect after authorization

        Returns:
            str: OAuth authorization URL
        """
        scopes = [
            "payments.create",
            "payments.read",
            "payment_links.create",
            "payment_links.read",
        ]

        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(scopes),
        }

        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.base_url}/oauth/authorize?{query}"

    async def exchange_code_for_token(self, code: str, redirect_uri: str) -> Dict:
        """Exchange authorization code for access token.

        Args:
            code: Authorization code from callback
            redirect_uri: Same redirect URI used in authorization

        Returns:
            dict: Token response
        """
        import httpx

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{self.base_url}/oauth/token",
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": redirect_uri,
                }
            )
            return resp.json()

    # -----------------------------------------------------------------------
    # Payment Creation
    # -----------------------------------------------------------------------

    async def create_payment(
        self,
        amount: int,
        currency: str = "ZAR",
        description: str = "",
        reference: str = "",
        customer_email: Optional[str] = None,
    ) -> Dict:
        """Create a payment request.

        Args:
            amount: Amount in cents (e.g., 250000 = R2,500.00)
            currency: ZAR (default)
            description: Payment description
            reference: Your reference (e.g., subscription ID)
            customer_email: Customer's email (optional)

        Returns:
            dict: Payment response with URL or error
        """
        import httpx

        if not self.access_token:
            return {"error": "Not authenticated — call authenticate_with_playwright first"}

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await client.post(
                    f"{self.api_url}/v1/payments",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "amount": amount,
                        "currency": currency,
                        "description": description,
                        "reference": reference,
                        "customer": {
                            "email": customer_email
                        } if customer_email else None,
                    }
                )
                return resp.json()
            except httpx.HTTPError as e:
                return {"error": f"API error: {e.response.status_code if hasattr(e, 'response') else str(e)}"}

    async def create_payment_link(
        self,
        amount: int,
        description: str,
        reference: str,
        currency: str = "ZAR",
        expires_at: Optional[datetime] = None,
    ) -> Dict:
        """Create a shareable payment link.

        Args:
            amount: Amount in cents
            description: Payment description
            reference: Your reference
            currency: ZAR (default)
            expires_at: Optional expiry datetime

        Returns:
            dict: Payment link URL
        """
        import httpx

        if not self.access_token:
            return {"error": "Not authenticated"}

        payload = {
            "amount": amount,
            "currency": currency,
            "description": description,
            "reference": reference,
        }

        if expires_at:
            payload["expires_at"] = expires_at.isoformat()

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await client.post(
                    f"{self.api_url}/v1/payment_links",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "Content-Type": "application/json",
                    },
                    json=payload
                )
                data = resp.json()
                return {
                    "url": data.get("url"),
                    "id": data.get("id"),
                    "status": data.get("status"),
                }
            except httpx.HTTPError as e:
                return {"error": f"API error: {e.response.status_code}"}

    # -----------------------------------------------------------------------
    # Subscription Billing (for StudEx AI monthly plans)
    # -----------------------------------------------------------------------

    async def create_subscription(
        self,
        customer_email: str,
        amount: int,
        description: str,
        reference: str,
        interval: str = "monthly",  # monthly | weekly | annually
    ) -> Dict:
        """Create a recurring subscription.

        Args:
            customer_email: Customer's email
            amount: Amount in cents per interval
            description: Subscription description
            reference: Your subscription ID
            interval: Billing interval (default: monthly)

        Returns:
            dict: Subscription details
        """
        import httpx

        if not self.access_token:
            return {"error": "Not authenticated"}

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await client.post(
                    f"{self.api_url}/v1/subscriptions",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "customer": {"email": customer_email},
                        "amount": amount,
                        "currency": "ZAR",
                        "description": description,
                        "reference": reference,
                        "interval": interval,
                    }
                )
                return resp.json()
            except httpx.HTTPError as e:
                return {"error": f"API error: {e.response.status_code}"}

    # -----------------------------------------------------------------------
    # Payment Status & Webhooks
    # -----------------------------------------------------------------------

    async def get_payment_status(self, payment_id: str) -> Dict:
        """Get payment status by ID."""
        import httpx

        if not self.access_token:
            return {"error": "Not authenticated"}

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await client.get(
                    f"{self.api_url}/v1/payments/{payment_id}",
                    headers={"Authorization": f"Bearer {self.access_token}"}
                )
                return resp.json()
            except httpx.HTTPError as e:
                return {"error": f"API error: {e.response.status_code}"}

    async def verify_webhook(self, payload: dict, signature: str) -> bool:
        """Verify webhook signature from Stitch.

        Args:
            payload: Webhook payload
            signature: X-Stitch-Signature header

        Returns:
            bool: True if valid
        """
        import hmac
        import hashlib

        expected_signature = hmac.new(
            self.client_secret.encode("utf-8"),
            json.dumps(payload, sort_keys=True).encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected_signature, signature)

    # -----------------------------------------------------------------------
    # Pricing Helpers (StudEx AI Plans)
    # -----------------------------------------------------------------------

    def get_plan_amount(self, plan: str) -> int:
        """Get plan amount in cents.

        Plans:
        - starter: R2,500/month
        - pro: R5,000/month
        - enterprise: R15,000/month
        """
        plans = {
            "starter": 250000,      # R2,500
            "pro": 500000,          # R5,000
            "enterprise": 1500000,  # R15,000
        }
        return plans.get(plan, 250000)

    async def create_subscription_link(
        self,
        plan: str,
        customer_email: str,
        reference: str,
    ) -> Dict:
        """Create a subscription link for a StudEx AI plan.

        Args:
            plan: Plan name (starter, pro, enterprise)
            customer_email: Customer email
            reference: Subscription reference

        Returns:
            dict: Payment link URL
        """
        amount = self.get_plan_amount(plan)
        description = f"StudEx AI {plan.capitalize()} Plan - Monthly"

        return await self.create_payment_link(
            amount=amount,
            description=description,
            reference=reference,
        )


# ---------------------------------------------------------------------------
# FastAPI Routes
# ---------------------------------------------------------------------------

def setup_stitch_routes(app):
    """Add Stitch payment routes to FastAPI app."""
    from fastapi import Request, HTTPException
    from pydantic import BaseModel

    stitch = StitchService()

    class PaymentRequest(BaseModel):
        amount: int
        description: str
        reference: str
        customer_email: Optional[str] = None

    class SubscriptionRequest(BaseModel):
        plan: str
        customer_email: str
        reference: str

    @app.post("/api/payments/stitch/create")
    async def create_payment_endpoint(req: PaymentRequest):
        """Create a Stitch payment."""
        result = await stitch.create_payment(
            amount=req.amount,
            description=req.description,
            reference=req.reference,
            customer_email=req.customer_email,
        )
        if "error" in result:
            raise HTTPException(400, result["error"])
        return result

    @app.post("/api/payments/stitch/subscription")
    async def create_subscription_endpoint(req: SubscriptionRequest):
        """Create a Stitch subscription for a StudEx AI plan."""
        result = await stitch.create_subscription_link(
            plan=req.plan,
            customer_email=req.customer_email,
            reference=req.reference,
        )
        if "error" in result:
            raise HTTPException(400, result["error"])
        return result

    @app.post("/api/payments/stitch/webhook")
    async def stitch_webhook(request: Request):
        """Handle Stitch webhook events."""
        body = await request.json()
        signature = request.headers.get("X-Stitch-Signature", "")

        if not await stitch.verify_webhook(body, signature):
            raise HTTPException(401, "Invalid webhook signature")

        # Process webhook event
        event_type = body.get("type")
        event_data = body.get("data", {})

        print(f"Stitch webhook: {event_type}", event_data)

        # TODO: Handle events (payment.successful, subscription.cancelled, etc.)

        return {"status": "ok"}
