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
                    StringManager.get(StringType.ERROR, "response.status.generic", error=error_msg)
                )
                return

            status = status_result["status"]
            
            # Hole Status-Text aus strings.json
            status_text = StringManager.get(StringType.APPENDIX, f"response.status.{status}")
            
            # Kombiniere mit generic Message
            message = StringManager.get(StringType.ANSWER, "response.status.generic", status=status_text)
            await interaction.followup.send(message)
            logger.info(f"Status command used by {interaction.user.id}: {status}")

        except Exception as e:
            logger.error(f"Error occurred in status command: {e}")
            await interaction.followup.send(
                StringManager.get(StringType.ERROR, "response.status.generic", error=str(e))
            )

async def setup(bot):
    await bot.add_cog(StatusCog(bot))