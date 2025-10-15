from discord.ext import commands
from discord import app_commands
import discord
from src.config_manager import StringManager, StringType
from src.discord_bot.util.check_status import check_status
from src.boot_service import boot_service
from src.discord_bot.logs.rl_log.log_handler import RelevanceLogger, LogType

from src.discord_bot.constant import GUILD_ID

class RebootCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.guilds(GUILD_ID)
    @app_commands.command(name="reboot", description="Reboot CL4P-TP.")
    @app_commands.default_permissions(administrator=True)
    async def reboot(self, interaction: discord.Interaction):
        status = check_status()
        if status == "starting":
            await interaction.response.send_message(StringManager.get_string(StringType.ERROR, "response.reboot.error").replace("{error}", StringManager.get_string(StringType.ERROR, "response.request.deny.starting")))
            RelevanceLogger.write_log_entry(f"cmd.reboot - failed (already starting)", interaction.user, LogType.INFO)
            return
            
        boot_result = boot_service.reboot()
        if boot_result["success"] == True:
            await interaction.response.send_message(StringManager.get_string(StringType.SUCCESS, "response.reboot.success"))
            RelevanceLogger.write_log_entry(f"cmd.reboot - success", interaction.user, LogType.INFO)
        else:
            await interaction.response.send_message(StringManager.get_string(StringType.ERROR, "response.reboot.error").replace("{error}", boot_result["error"]))
            RelevanceLogger.write_log_entry(f"cmd.reboot - failed ({boot_result['error']})", interaction.user, LogType.WARNING)

async def setup(bot):
    await bot.add_cog(RebootCog(bot))