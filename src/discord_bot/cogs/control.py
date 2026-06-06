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
        # Temporary - until command updated for multiple hosts
        host_type = "hardware"
        hostname = "claptp"
        
        await interaction.response.defer()

        try:
            # 1) Load user from database to get rights level
            user = self.user_service.get_user(interaction.user.id)
            if not user:
                await interaction.followup.send(
                    StringManager.get(StringType.WARN, "error.unknown_user")
                )
                logger.warning(f"User {interaction.user.id} not found in database")
                return
            
            rights_level = RightsLevel(user.get("boot_rights_level", RightsLevel.BASIC.value))
            
            # 2) Initialize handler with user rights
            request_handler = BootRequestHandler(
                host_type=host_type,
                host_name=hostname,
                rights_level=rights_level
            )
            
            # 3) Handle request
            result = request_handler.handle_request(interaction.user.id, action)
        
            # 4) Check if request was successful
            if not result.get("success", False):
                reason = result.get("reason", "unknown_error")

                if reason == "cooldown":
                    reason_text = StringManager.get(
                        StringType.APPENDIX,
                        f"response.request.deny.reasons.{reason}",
                        m=result.get("m", 0),
                        s=result.get("s", 0)
                    )
                elif reason == "boot_state":
                    reason_text = StringManager.get(
                        StringType.APPENDIX,
                        f"response.request.deny.reasons.{reason}",
                        hostname=hostname,
                        state=result.get("state", "unknown")
                    )
                elif reason == "starting":
                    reason_text = StringManager.get(
                        StringType.APPENDIX,
                        f"response.request.deny.reasons.{reason}",
                        hostname=hostname
                    )
                elif reason == "unknown_error":
                    reason_text = StringManager.get(
                        StringType.APPENDIX,
                        f"response.request.deny.reasons.{reason}",
                        error=result.get("error", "unknown")
                    )
                else:
                    reason_text = StringManager.get(
                        StringType.APPENDIX,
                        f"response.request.deny.reasons.{reason}"
                    )
                
                message = StringManager.get(
                    StringType.DENY,
                    "response.request.deny.generic",
                    reason=reason_text
                )
                await interaction.followup.send(message)
                logger.warning(f"Boot request '{action}' from user {interaction.user.id} failed: {reason}")
                return
            
            # 5) Check approval status
            if result.get("status") == BootRequestStatus.APPROVED.value:
                action_text = StringManager.get(
                    StringType.APPENDIX,
                    f"response.request.success.{action}"
                )
                await interaction.followup.send(
                    StringManager.get(
                        StringType.SUCCESS,
                        "response.request.success.generic",
                        action=action_text
                    )
                )
                logger.info(f"Boot request '{action}' from user {interaction.user.id} approved")
            else:
                # Request was rejected by restrictions
                reason = result.get("reason", "unknown")
                reason_text = StringManager.get(
                    StringType.APPENDIX,
                    f"response.request.deny.reasons.{reason}"
                )
                message = StringManager.get(
                    StringType.DENY,
                    "response.request.deny.generic",
                    reason=reason_text
                )
                await interaction.followup.send(message)
                logger.warning(f"Boot request '{action}' from user {interaction.user.id} rejected: {reason}")
        
        except Exception as e:
            logger.error(f"Error handling boot request from user {interaction.user.id}: {e}")
            await interaction.followup.send(
                StringManager.get(StringType.WARN, "response.request.deny.generic", reason="Unbekannter Fehler")
            )

async def setup(bot):
    await bot.add_cog(ControlCog(bot))