import discord
from discord.ext import commands
from discord import app_commands
import logging
from typing import Literal
from datetime import datetime

from src.config_manager import ConfigManager, StringManager, StringType
from src.discord_bot.services.boot_request_handler import BootRequestHandler
from src.models import RightsLevel
from src.util.db.database_manager import DatabaseManager

logger = logging.getLogger(__name__)
GUILD_ID = discord.Object(id=int(ConfigManager.get("discord.guild_id")))

class ControlCog(commands.Cog):
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
            rights_level = DatabaseManager.get("discord", "user", {"discord_id": int(interaction.user.id)}, "rights_level")
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
            if result.get("pass"):
                hostname_alias = StringManager.get(StringType.VALUE, f"hostname_alias.{hostname}", default=hostname)
                await interaction.followup.send(StringManager.get(StringType.SUCCESS, "response.request.success", action=action.capitalize(), hostname=hostname_alias))

                # Enter boot request
                boot_request = {
                    "requested": True,
                    "action": action,
                    "timestamp": datetime.now(),
                }
                DatabaseManager.set("host", host_type, {"hostname": hostname}, {"boot.request": boot_request})


                logger.info(f"Boot request '{action}' for {hostname} from user {interaction.user.id} approved and executed.")
                return
            else:
                hostname = StringManager.get(StringType.VALUE, f"hostname_alias.{hostname}", default=hostname)
                reason = StringManager.get(StringType.VALUE, f"response.request.deny.reasons.{result['reason']['type']}", hostname=hostname, **result["reason"])
                message = StringManager.get(StringType.DENY, "response.request.deny.generic", reason=reason if "reason" in result else "Unbekannter Grund")
                await interaction.followup.send(message)
                logger.warning(f"Boot request '{action}' for {hostname} from user {interaction.user.id} denied.")
                return


        except Exception as e:
            logger.error(f"Error handling boot request from user {interaction.user.id}: {str(e)}")
            await interaction.followup.send(
                StringManager.get(StringType.WARN, "response.request.deny.generic", reason="Unbekannter Fehler")
            )

async def setup(bot):
    await bot.add_cog(ControlCog(bot))