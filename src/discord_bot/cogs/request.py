import discord
from discord.ext import commands
from discord import app_commands
import logging
import asyncio
from typing import Literal
from datetime import datetime

from src.config_manager import ConfigManager, StringManager, StringType
from src.discord_bot.services.boot_request_handler import BootRequestHandler
from src.discord_bot.checks import get_rights_level
from src.models import RightsLevel
from src.util.db.database_manager import DatabaseManager

logger = logging.getLogger(__name__)
GUILD_ID = discord.Object(id=int(ConfigManager.get("discord.guild_id")))

# Time waiting for boot manager to repond before giving up
REQUEST_POLL_INTERVAL = 1.5
REQUEST_POLL_TIMEOUT = 20

class RequestCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="request", description="Request a boot action")
    @app_commands.guilds(GUILD_ID)
    async def request(
        self, 
        interaction: discord.Interaction,
        action: Literal["start", "stop", "restart", "kill"],
        host_type: Literal["hardware", "vm"] = "hardware",
        hostname: Literal["claptp", "example", "vm100-minecraft"] = "claptp"
    ):

        await interaction.response.defer()

        try:
            # 1) Load user from database to get rights level
            rights_level = get_rights_level(interaction.user.id)
            if not rights_level:
                await interaction.followup.send(StringManager.get(StringType.WARN, "error.unknown_user"))
                logger.warning(f"Boot request from unknown user {interaction.user.id}")
                return

            # if action = "Kill", RightsLevel must be ADMIN
            if action == "kill" and rights_level != RightsLevel.ADMIN:
                await interaction.followup.send(StringManager.get(StringType.WARN, "error.no_permission"))
                return

            # 2) Request handler
            result = BootRequestHandler.handle_request(
                host_type=host_type,
                hostname=hostname,
                action=action
            )
        
            # 4) Check if request was successful
            if not result["success"]:
                message = StringManager.get(StringType.DENY, f"error.{result['error']['type']}", e=result["error"].get("e"))
                await interaction.followup.send(message)
                logger.warning(f"Boot request '{action}' from user {interaction.user.id} failed: {result['error']['type']}")
                return

            # 5) Check approval status
            if not result.get("pass"):
                alias = StringManager.get(StringType.VALUE, f"hostname_alias.{hostname}", default=hostname)
                reason = StringManager.get(
                    StringType.VALUE, f"response.request.deny.reasons.{result['reason']['type']}",
                    hostname=alias, **result["reason"]
                )
                message = StringManager.get(StringType.DENY, "response.request.deny.generic", reason=reason)
                await interaction.followup.send(message)
                logger.warning(f"Boot request '{action}' for host '{hostname}' from user {interaction.user.id} denied")
                return

            alias = StringManager.get(StringType.VALUE, f"hostname_alias.{hostname}", default=hostname)
            boot_request = {
                "requested": True,
                "action": action,
                "state": "pending",
                "requested_by": interaction.user.id,
                "timestamp": datetime.now(),
                "started_at": None,
                "finished_at": None,
                "error": None
            }
            DatabaseManager.set("host", host_type, {"hostname": hostname}, {"boot.request": boot_request})

            status_message = await interaction.followup.send(StringManager.get(StringType.INFO, "response.request.pending", action=action.capitalize(), hostname=alias))
            logger.info(f"Boot request '{action}' for '{hostname}' for user {interaction.user.id} enqueued.")

            await self._await_result(status_message, host_type, hostname, action, alias)

        except Exception as e:
            logging.error(f"Error handling boot request from user {interaction.user.id}: {str(e)}", exc_info=True)
            await interaction.followup.send(StringManager.get(StringType.WARN, "response.request.deny.generic", reason="Unbekannter Fehler"))

    async def _await_result(self, status_message: discord.Message, host_type: str, hostname: str, action: str, alias: str):
        elapsed = 0.0
        while elapsed < REQUEST_POLL_TIMEOUT:
            await asyncio.sleep(REQUEST_POLL_INTERVAL)
            elapsed += REQUEST_POLL_INTERVAL

            state = DatabaseManager.get("host", host_type, {"hostname": hostname}, "boot.request.state")

            if state == "success":
                await status_message.edit(content=StringManager.get(
                    StringType.SUCCESS, "response.request.success", action=action.capitalize(), hostname=alias
                ))
                return

            if state == "failed":
                error = DatabaseManager.get(
                    "host", host_type, {"hostname": hostname}, "boot.request.error", default="Unbekannter Fehler"
                )
                await status_message.edit(content=StringManager.get(
                    StringType.WARN, "response.request.failed", action=action.capitalize(), hostname=alias, error=error
                ))
                return

        await status_message.edit(content=StringManager.get(
            StringType.WARN, "response.request.timeout", action=action.capitalize(), hostname=alias
        ))

async def setup(bot):
    await bot.add_cog(RequestCog(bot))
