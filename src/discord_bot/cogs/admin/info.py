# 4 later 
# save hard/software info to mqtt before

from src.discord_bot.logs.rl_log.log_handler import RelevanceLogger, LogType
import discord
from discord import app_commands
from discord.ext import commands

from src.discord_bot.constant import GUILD_ID

class InfoCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.guilds(GUILD_ID)
    @app_commands.command(name="info", description="Zeigt hard- & softwareInformationen über CL4P-TP an.")
    @app_commands.default_permissions(administrator=True)
    async def info(self, interaction: discord.Interaction):
        await interaction.response.send_message("Command not implemented yet.", ephemeral=True, delete_after=10)
        RelevanceLogger.write_log_entry(f"cmd.info - executed", interaction.user.id, LogType.INFO)

async def setup(bot):
    await bot.add_cog(InfoCog(bot))