import discord
from discord.ext import commands
from discord import app_commands
import logging
from typing import Literal

from src.config_manager import ConfigManager, StringManager, StringType
from src.discord_bot.services.boot_request_handler import BootRequestHandler

logger = logging.getLogger(__name__)
GUILD_ID = discord.Object(id=int(ConfigManager.get_config("discord.guild_id")))

class ControlCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.request_handler = BootRequestHandler()

    @app_commands.command(name="request", description="Request a boot action")
    @app_commands.guilds(GUILD_ID)
    async def request(
        self, 
        interaction: discord.Interaction,
        action: Literal["start", "stop"]
    ):
        await interaction.response.defer()

        try:
            result = self.request_handler.handle_request(interaction.user.id, action)
        
            if result["status" == "approved"]:
                reason = result.get("reason", "unknown")
                await interaction.followup.send(StringManager.get(StringType.SUCCESS, "response.request.success.generic", action=action))
                logger.info(f"Boot request '{action}' from user {interaction.user.id} approved: {reason}")
            else:
                reason = result.get("reason", "unknown")
                await interaction.followup.send(StringManager.get(StringType.ERROR, "response.request.deny.generic"))
                logger.info(f"Boot request '{action}' from user {interaction.user.id} denied: {reason}")
        
        except Exception as e:
            logger.error(f"Error handling boot request from user {interaction.user.id}: {e}")
            await interaction.followup.send(StringManager.get(StringType.ERROR, "response.request.deny.generic"))

async def setup(bot):
    await bot.add_cog(ControlCog(bot))