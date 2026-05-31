import discord
from discord.ext import commands
from discord import app_commands
import logging
from typing import Literal

from src.config_manager import ConfigManager, StringManager, StringType
from src.discord_bot.services.boot_request_handler import BootRequestHandler
from src.discord_bot.services.user_service import UserService
from src.models import RightsLevel, BootRequestStatus

logger = logging.getLogger(__name__)
GUILD_ID = discord.Object(id=int(ConfigManager.get_config("discord.guild_id")))

class ControlCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user_service = UserService()

    @app_commands.command(name="request", description="Request a boot action")
    @app_commands.guilds(GUILD_ID)
    async def request(
        self, 
        interaction: discord.Interaction,
        action: Literal["start", "stop"]
    ):
        await interaction.response.defer()

        try:
            # 1) Load user from database to get rights level
            user = self.user_service.get_user(interaction.user.id)
            if not user:
                await interaction.followup.send(StringManager.get(StringType.ERROR, "response.request.deny.generic"))
                logger.warning(f"User {interaction.user.id} not found in database")
                return
            
            rights_level = RightsLevel(user.get("boot_rights_level", RightsLevel.BASIC.value))
            
            # 2) Initialize handler with user rights
            request_handler = BootRequestHandler(rights_level=rights_level)
            
            # 3) Handle request
            result = request_handler.handle_request(interaction.user.id, action)
        
            # 4) Check response
            if not result.get("success", False):
                await interaction.followup.send(StringManager.get(StringType.ERROR, "response.request.deny.generic"))
                logger.warning(f"Boot request '{action}' from user {interaction.user.id} failed: {result.get('error', 'unknown')}")
                return
            
            # 5) Check approval status
            if result.get("status") == BootRequestStatus.APPROVED.value:
                reason = result.get("reason", "unknown")
                await interaction.followup.send(StringManager.get(StringType.SUCCESS, "response.request.success.generic", action=action))
                logger.info(f"Boot request '{action}' from user {interaction.user.id} approved: {reason}")
            else:
                reason = result.get("reason", "unknown")
                await interaction.followup.send(StringManager.get(StringType.ERROR, "response.request.deny.generic"))
                logger.warning(f"Boot request '{action}' from user {interaction.user.id} denied: {reason}")
        
        except Exception as e:
            logger.error(f"Error handling boot request from user {interaction.user.id}: {e}")
            await interaction.followup.send(StringManager.get(StringType.ERROR, "response.request.deny.generic"))

async def setup(bot):
    await bot.add_cog(ControlCog(bot))