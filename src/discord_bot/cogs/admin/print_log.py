import os
import discord
from discord.ext import commands 
from discord import app_commands
from src.config_manager import StringManager, StringType
from src.discord_bot.logs.rl_log.log_handler import RelevanceLogger, LogType

from src.discord_bot.constant import GUILD_ID

class PrintLogCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.guilds(GUILD_ID)
    @app_commands.command(name="print_log", description="Sendet die Log-Dateien als Anhang.")
    # app permission, if user has specific role
    @app_commands.default_permissions()
    async def print_log(self, interaction: discord.Interaction):
        log_dir = './src/discord_bot/logs/rl_log'
        log_files = [f for f in os.listdir(log_dir) if os.path.isfile(os.path.join(log_dir, f))]
        
        # no log files
        if not log_files:
            await interaction.response.send_message(StringManager.get_string(StringType.WARNING, "response.print_log.no_files"))
            RelevanceLogger.write_log_entry(f"cmd.print_log - failed (no log files)", interaction.user, LogType.INFO)
            return
        log_files.sort() 
        log_file_paths = [os.path.join(log_dir, f) for f in log_files]
        try:
            # Erst antworten (defer), dann followup mit Dateien
            await interaction.response.defer(ephemeral=True)
            files = [discord.File(fp) for fp in log_file_paths if fp.endswith('.log')]
            await interaction.followup.send(content="Hier sind die Log-Dateien:", files=files, ephemeral=True)
            RelevanceLogger.write_log_entry(f"cmd.print_log - success", interaction.user, LogType.INFO)
        except Exception as e:
            await interaction.followup.send(StringManager.get_string(StringType.ERROR, "response.print_log.error", error=str(e)), ephemeral=True)
            RelevanceLogger.write_log_entry(f"cmd.print_log - failed (error: {str(e)})", interaction.user, LogType.WARNING)
        return
    
async def setup(bot):
    await bot.add_cog(PrintLogCog(bot))