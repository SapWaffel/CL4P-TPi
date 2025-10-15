import discord
from discord import app_commands
from discord.ext import commands
from src.config_manager import ConfigManager, StringManager, StringType
from src.discord_bot.logs.rl_log.log_handler import RelevanceLogger, LogType

from src.discord_bot.constant import GUILD_ID

class ReloadCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.guilds(GUILD_ID)
    @app_commands.command(name="reload", description="Startet den bot neu.")
    @app_commands.default_permissions(administrator=True)
    async def reload(self, interaction: discord.Interaction):
        await interaction.response.defer()
        message = await interaction.followup.send(
            StringManager.get_string(StringType.PROCESSING, "response.reload.start"),
            wait=True
        )
        ConfigManager.merge_config(module="discord_bot", new_data={"reload_response": {"waiting_for_response": True, "channel": interaction.channel.id, "user": interaction.user.id, "message": message.id } })
        RelevanceLogger.write_log_entry(f"cmd.reload - success, restarting", interaction.user, LogType.INFO)
        await interaction.client.close()

async def setup(bot):
    await bot.add_cog(ReloadCog(bot))