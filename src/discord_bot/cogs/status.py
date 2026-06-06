import discord
from discord.ext import commands
from discord import app_commands
import logging

from src.config_manager import ConfigManager, StringManager, StringType
from src.discord_bot.services.status_service import StatusService

logger = logging.getLogger(__name__)
GUILD_ID = discord.Object(id=int(ConfigManager.get_config("discord.guild_id")))

class StatusCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="status", description="Get the boot status of a host")
    @app_commands.guilds(GUILD_ID)
    async def status(self, interaction: discord.Interaction):
        await interaction.response.defer()

        try:
            status_service = StatusService()
            status_result = status_service.get_boot_status()

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

            hostname_key = status_result.get("hostname", "claptp")
            hostname_alias = StringManager.get(
                StringType.APPENDIX,
                f"response.status.hostname_alias.{hostname_key}"
            )

            if hostname_alias == f"Missing string for key: response.status.hostname_alias.{hostname_key}" or "Invalid string path" in hostname_alias:
                hostname_alias = hostname_key

            status = status_result.get("status", "unknown")

            status_text = StringManager.get(
                StringType.APPENDIX,
                f"response.status.{status}"
            )

            message = StringManager.get(
                StringType.ANSWER,
                "response.status.generic",
                hostname=hostname_alias,
                status=status_text
            )
            await interaction.followup.send(message)
            logger.info(f"Status command used by {interaction.user.id}: {status}")

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