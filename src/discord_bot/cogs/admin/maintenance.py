import discord
from discord.ext import commands
from discord import app_commands
from src.config_manager import ConfigManager, StringManager, StringType
from src.discord_bot.util.refresh_presence import refresh_presence
from src.discord_bot.logs.rl_log.log_handler import RelevanceLogger, LogType

from src.discord_bot.constant import GUILD_ID

class MaintenanceCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.guilds(GUILD_ID)
    @app_commands.command(name="maintenance", description="Toggles maintenance mode.")
    @app_commands.default_permissions(administrator=True)
    async def maintenance(self, interaction: discord.Interaction):
        current_maintenance = ConfigManager.get_config('discord_bot').get('maintenance', False)
        new_maintenance = not current_maintenance
        try:
            ConfigManager.merge_config('discord_bot', {'maintenance': new_maintenance})
        except Exception as e:
            await interaction.response.send_message(StringManager.get_string(StringType.ERROR, "response.maintenance.error", error=str(e)))
            RelevanceLogger.write_log_entry(f"cmd.maintenance - failed (error: {str(e)})", interaction.user, LogType.WARNING)
            return

        await interaction.response.send_message(StringManager.get_string(StringType.SUCCESS, f"response.maintenance.{str(new_maintenance).lower()}"))
        RelevanceLogger.write_log_entry(f"cmd.maintenance - success (set to {new_maintenance})", interaction.user, LogType.INFO)
        await refresh_presence(self.bot)

async def setup(bot):
    await bot.add_cog(MaintenanceCog(bot))
