import discord
from discord.ext import commands
from discord import app_commands
from src.config_manager import StringManager, StringType
from src.boot_service import boot_service
from src.discord_bot.util.check_status import check_status
from src.discord_bot.logs.rl_log.log_handler import RelevanceLogger, LogType

from src.discord_bot.constant import GUILD_ID

class BootCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.guilds(GUILD_ID)
    @app_commands.default_permissions(administrator=True)
    @app_commands.command(name="boot", description="Boot-toggled CL4P-TP.")
    async def boot(self, interaction: discord.Interaction):
        status = check_status()
        if status == "starting":
            await interaction.response.send_message(StringManager.get_string(StringType.WARNING, "response.boot.error", error=StringManager.get_string(StringType.APPENDIX, "response.request.deny.already_starting")))
            RelevanceLogger.write_log_entry(f"cmd.boot - failed (already starting)", interaction.user, LogType.INFO)
            return
        
        boot_result = boot_service.boot()
        if boot_result["success"] == True:
            await interaction.response.send_message(StringManager.get_string(StringType.SUCCESS, "response.boot.success"))
            RelevanceLogger.write_log_entry(f"cmd.boot - success", interaction.user, LogType.INFO)
        else:
            await interaction.response.send_message(StringManager.get_string(StringType.ERROR, "response.boot.error", error=boot_result["error"]))
            RelevanceLogger.write_log_entry(f"cmd.boot - failed ({boot_result['error']})", interaction.user, LogType.WARNING)

async def setup(bot):
    await bot.add_cog(BootCog(bot))