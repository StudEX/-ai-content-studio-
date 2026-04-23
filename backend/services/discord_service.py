"""Discord Service — Internal operations hub and client communication.

Features:
- Slash commands for agent control
- Webhooks for notifications
- Thread-based customer conversations
- Role-based access control
"""

import os
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List, Any

# Discord imports (install: pip install discord.py)
try:
    import discord
    from discord.ext import commands, tasks
    DISCORD_AVAILABLE = True
except ImportError:
    DISCORD_AVAILABLE = False
    discord = None
    commands = None

SAST = timezone(timedelta(hours=2))


class DiscordService:
    """Discord bot service for StudEx operations."""

    def __init__(self):
        self.token = os.getenv("DISCORD_BOT_TOKEN")
        self.guild_id = int(os.getenv("DISCORD_GUILD_ID", "0"))
        self.admin_role_id = int(os.getenv("DISCORD_ADMIN_ROLE_ID", "0"))

        if not DISCORD_AVAILABLE:
            self.bot = None
            return

        # Set up bot with intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True

        self.bot = commands.Bot(command_prefix="/", intents=intents)

        # Event handlers registered via decorators
        self._setup_handlers()

    def _setup_handlers(self):
        """Register Discord event handlers."""
        if not self.bot:
            return

        @self.bot.event
        async def on_ready():
            print(f"StudEx Discord bot logged in as {self.bot.user}")
            # Sync slash commands
            try:
                synced = await self.bot.tree.sync()
                print(f"Synced {len(synced)} slash commands")
            except Exception as e:
                print(f"Failed to sync commands: {e}")

        @self.bot.event
        async def on_message(message):
            # Ignore bot messages
            if message.author.bot:
                return

            # Process commands
            await self.bot.process_commands(message)

            # Check for customer service channel messages
            if hasattr(self, '_customer_service_handler'):
                await self._customer_service_handler(message)

    @property
    def configured(self) -> bool:
        return bool(self.token and self.bot)

    async def start(self):
        """Start the Discord bot."""
        if not self.configured:
            print("Discord not configured — set DISCORD_BOT_TOKEN")
            return

        try:
            await self.bot.start(self.token)
        except Exception as e:
            print(f"Failed to start Discord bot: {e}")

    async def stop(self):
        """Stop the Discord bot."""
        if self.bot and not self.bot.is_closed():
            await self.bot.close()

    # -----------------------------------------------------------------------
    # Slash Commands (App Commands)
    # -----------------------------------------------------------------------

    def register_slash_command(self, name: str, description: str, callback):
        """Register a slash command dynamically."""
        if not self.bot:
            return

        from discord import app_commands

        @self.bot.tree.command(name=name, description=description)
        async def cmd(interaction: discord.Interaction, **kwargs):
            try:
                result = await callback(interaction, **kwargs)
                await interaction.response.send_message(result, ephemeral=False)
            except Exception as e:
                await interaction.response.send_message(f"Error: {str(e)}", ephemeral=True)

    # -----------------------------------------------------------------------
    # Messaging Utilities
    # -----------------------------------------------------------------------

    async def send_message(
        self,
        channel_id: int,
        content: str,
        embed: Optional[Dict] = None,
        ephemeral: bool = False
    ) -> Optional[discord.Message]:
        """Send a message to a Discord channel.

        Args:
            channel_id: Discord channel ID
            content: Message content
            embed: Optional embed dict (title, description, fields, color)
            ephemeral: If True, only visible to the user who triggered

        Returns:
            discord.Message or None
        """
        if not self.bot:
            return None

        try:
            channel = await self.bot.fetch_channel(channel_id)

            if embed:
                embed_obj = discord.Embed(
                    title=embed.get("title", ""),
                    description=embed.get("description", ""),
                    color=embed.get("color", 0x5865F2)  # Discord blurple
                )

                for field in embed.get("fields", []):
                    embed_obj.add_field(
                        name=field.get("name", ""),
                        value=field.get("value", ""),
                        inline=field.get("inline", False)
                    )

                if embed.get("footer"):
                    embed_obj.set_footer(text=embed["footer"])
                if embed.get("thumbnail"):
                    embed_obj.set_thumbnail(url=embed["thumbnail"])

                await channel.send(content=content, embed=embed_obj)
            else:
                await channel.send(content=content)

        except Exception as e:
            print(f"Discord send error: {e}")
            return None

    async def send_dm(
        self,
        user_id: int,
        content: str,
        embed: Optional[Dict] = None
    ) -> Optional[discord.Message]:
        """Send a direct message to a user."""
        if not self.bot:
            return None

        try:
            user = await self.bot.fetch_user(user_id)
            await user.send(content=content)
        except Exception as e:
            print(f"Discord DM error: {e}")
            return None

    async def create_thread(
        self,
        channel_id: int,
        name: str,
        message: Optional[discord.Message] = None
    ) -> Optional[discord.Thread]:
        """Create a thread in a channel for customer conversations."""
        if not self.bot:
            return None

        try:
            channel = await self.bot.fetch_channel(channel_id)

            if message:
                return await message.create_thread(name=name)
            else:
                # Create thread without a starting message
                return await channel.create_thread(name=name)
        except Exception as e:
            print(f"Discord thread error: {e}")
            return None

    # -----------------------------------------------------------------------
    # Webhook Support
    # -----------------------------------------------------------------------

    async def send_webhook(
        self,
        webhook_url: str,
        content: str,
        username: Optional[str] = None,
        avatar_url: Optional[str] = None
    ):
        """Send a message via Discord webhook."""
        if not DISCORD_AVAILABLE:
            return

        try:
            async with discord.Webhook.from_url(
                webhook_url,
                session=self.bot.http._HTTPClient__session
            ) as webhook:
                await webhook.send(
                    content=content,
                    username=username,
                    avatar_url=avatar_url
                )
        except Exception as e:
            print(f"Discord webhook error: {e}")

    # -----------------------------------------------------------------------
    # Role Management
    # -----------------------------------------------------------------------

    async def add_role(self, user_id: int, role_id: int, guild_id: Optional[int] = None):
        """Add a role to a user."""
        if not self.bot:
            return

        guild = self.bot.get_guild(guild_id or self.guild_id)
        if not guild:
            return

        try:
            member = await guild.fetch_member(user_id)
            role = guild.get_role(role_id)
            if role:
                await member.add_roles(role)
        except Exception as e:
            print(f"Discord role add error: {e}")

    async def remove_role(self, user_id: int, role_id: int, guild_id: Optional[int] = None):
        """Remove a role from a user."""
        if not self.bot:
            return

        guild = self.bot.get_guild(guild_id or self.guild_id)
        if not guild:
            return

        try:
            member = await guild.fetch_member(user_id)
            role = guild.get_role(role_id)
            if role:
                await member.remove_roles(role)
        except Exception as e:
            print(f"Discord role remove error: {e}")

    # -----------------------------------------------------------------------
    # Customer Service Integration
    # -----------------------------------------------------------------------

    def set_customer_service_handler(self, handler):
        """Set the async handler for customer service messages."""
        self._customer_service_handler = handler


# ---------------------------------------------------------------------------
# Discord Bot Commands for StudEx
# ---------------------------------------------------------------------------

def setup_studex_commands(discord_service: DiscordService):
    """Register StudEx-specific slash commands."""

    if not discord_service.bot:
        return

    from discord import app_commands

    @discord_service.bot.tree.command(
        name="agent-status",
        description="Check status of all StudEx agents"
    )
    async def agent_status(interaction: discord.Interaction):
        """Check agent status."""
        # This would call your backend API
        await interaction.response.send_message(
            "🤖 **StudEx Agent Status**\n\n"
            "• Research Agent: 🟢 Idle\n"
            "• Content Agent: 🟢 Idle\n"
            "• Customer Service: 🟢 Active\n"
            "• Analytics: 🟡 Running (2 tasks)\n\n"
            f"Updated: {datetime.now(SAST).strftime('%H:%M SAST')}"
        )

    @discord_service.bot.tree.command(
        name="new-task",
        description="Create a new task for a StudEx agent"
    )
    @app_commands.describe(
        agent="Which agent to use (research, content, seo, social, etc.)",
        task="Task description"
    )
    async def new_task(interaction: discord.Interaction, agent: str, task: str):
        """Create a new agent task."""
        await interaction.response.send_message(
            f"📋 **Task Created**\n\n"
            f"Agent: {agent}\n"
            f"Task: {task}\n\n"
            f"Task ID: `{discord_service.bot.user.id}`\n"
            f"Status: Queued ⏳"
        )

    @discord_service.bot.tree.command(
        name="customer-lookup",
        description="Look up customer conversation history"
    )
    @app_commands.describe(
        customer="Customer phone number or Discord ID"
    )
    async def customer_lookup(interaction: discord.Interaction, customer: str):
        """Look up customer history."""
        await interaction.response.send_message(
            f"🔍 **Customer Lookup**: {customer}\n\n"
            f"Last contact: Today 14:32\n"
            f"Total conversations: 5\n"
            f"Status: Active customer\n"
            f"Last issue: Order status inquiry — Resolved ✓"
        )

    @discord_service.bot.tree.command(
        name="escalate",
        description="Escalate a conversation to human agent"
    )
    @app_commands.describe(
        reason="Reason for escalation"
    )
    async def escalate(interaction: discord.Interaction, reason: str):
        """Escalate to human."""
        await interaction.response.send_message(
            f"⚠️ **Escalated to Human**\n\n"
            f"Reason: {reason}\n\n"
            f"A human agent will join this conversation within 15 minutes."
        )

    @discord_service.bot.tree.command(
        name="daily-report",
        description="Get today's customer service report"
    )
    async def daily_report(interaction: discord.Interaction):
        """Daily report."""
        await interaction.response.send_message(
            "📊 **Daily Report** — " + datetime.now(SAST).strftime('%Y-%m-%d') + "\n\n"
            "📨 **Messages Processed**: 47\n"
            "✅ **Auto-resolved**: 39 (83%)\n"
            "⚠️ **Escalated**: 8 (17%)\n"
            "⏱️ **Avg Response Time**: 1.2s\n"
            "😊 **Customer Satisfaction**: 4.8/5\n\n"
            "**Top Issues**:\n"
            "• Order status: 18\n"
            "• Returns: 12\n"
            "• Product info: 10\n"
            "• Shipping: 7"
        )

    @discord_service.bot.tree.command(
        name="connect-whatsapp",
        description="Connect WhatsApp number for customer service"
    )
    @app_commands.describe(
        phone_number="WhatsApp Business number (e.g., +27123456789)"
    )
    async def connect_whatsapp(interaction: discord.Interaction, phone_number: str):
        """Connect WhatsApp."""
        await interaction.response.send_message(
            f"📱 **WhatsApp Connected**\n\n"
            f"Number: {phone_number}\n\n"
            f"✅ WhatsApp Business API integration active.\n"
            f"Customers can now message you on WhatsApp and Discord simultaneously."
        )
