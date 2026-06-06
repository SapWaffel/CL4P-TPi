import discord
from discord.ext import commands
from discord import app_commands
import logging
from typing import Literal

from src.config_manager import ConfigManager, StringManager, StringType
from src.discord_bot.services.status_service import StatusService

logger = logging.getLogger(__name__)
GUILD_ID = discord.Object(id=int(ConfigManager.get("discord.guild_id")))

class StatusCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="status", description="Get the boot status of a host")
    @app_commands.guilds(GUILD_ID)
    async def status(
        self,
        interaction: discord.Interaction,
        host_type: Literal["hardware", "vm"] = "hardware",
        hostname: Literal["claptp", "vm100-minecraft"] = "claptp",
    ):
        await interaction.response.defer()

        try:
            status_service = StatusService()
            status_result = status_service.get_boot_status(host_type=host_type, hostname=hostname)

            if not status_result["success"]:
                error_msg = status_result.get("error", "unknown error")
                await interaction.followup.send(
                    StringManager.get(
                        StringType.WARN,
                        "response.status.error",
                        error=error_msg
                    )
                )
                return

            hostname = StringManager.get(
                StringType.APPENDIX, f"hostname_alias.{hostname}", default=hostname
            )
            status = status_result.get("status", "unknown")

            status_text = StringManager.get(
                StringType.APPENDIX,
                f"response.status.{status}"
            )

            message = StringManager.get(
                StringType.ANSWER,
                "response.status.generic",
                hostname=hostname,
                status=status_text
            )
            await interaction.followup.send(message)

        except Exception as e:
            logger.error(f"Error occurred in status command: {e}")
            await interaction.followup.send(
                StringManager.get(
                    StringType.WARN,
                    "response.status.error",
                    error=str(e)
                )
            )

async def setup(bot):
    await bot.add_cog(StatusCog(bot))