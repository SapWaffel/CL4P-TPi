import discord
from discord.ext import commands
from src.config_manager import ConfigManager, StringManager, StringType
from src.discord_bot.util.is_admin_on_guild import is_admin_on_guild
from src.discord_bot.util.refresh_presence import refresh_presence
from src.discord_bot.logs.rl_log.log_handler import RelevanceLogger, LogType

class MaintenanceCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.maintenance.admin_only = True

    @commands.command(name='maintenance', help='Toggled CL4P-TPs Wartungsmodus.')
    @commands.dm_only()
    async def maintenance(self, ctx):
        if not await is_admin_on_guild(self.bot, ctx.author.id):
            await ctx.send(StringManager.get_string(StringType.ERROR, "error.no_permission"))
            RelevanceLogger.write_log_entry(f"cmd.maintenance - failed (no permission)", ctx.author.id, LogType.INFO)
            return
        
        current_maintenance = ConfigManager.get_config('discord_bot').get('maintenance', False)
        new_maintenance = not current_maintenance
        try:
            ConfigManager.merge_config('discord_bot', {'maintenance': new_maintenance})
        except Exception as e:
            await ctx.send(StringManager.get_string(StringType.ERROR, "response.maintenance.error", error=str(e)))
            RelevanceLogger.write_log_entry(f"cmd.maintenance - failed (error: {str(e)})", ctx.author.id, LogType.WARNING)
            return

        await ctx.send(StringManager.get_string(StringType.SUCCESS, "response.maintenance", status=str(new_maintenance).lower()))
        RelevanceLogger.write_log_entry(f"cmd.maintenance - success (set to {new_maintenance})", ctx.author.id, LogType.INFO)
        await refresh_presence(self.bot)

async def setup(bot):
    await bot.add_cog(MaintenanceCog(bot))