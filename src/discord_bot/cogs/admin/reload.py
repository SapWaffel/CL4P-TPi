from discord.ext import commands
from src.discord_bot.util.is_admin_on_guild import is_admin_on_guild
from src.config_manager import ConfigManager
from src.discord_bot.logs.rl_log.log_handler import RelevanceLogger, LogType
import os, sys

class ReloadCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reload.admin_only = True

    @commands.command(name='reload', help='Startet den Discord-Bot neu.')
    @commands.dm_only()
    async def reload(self, ctx):
        if not await is_admin_on_guild(self.bot, ctx.author.id):
            await ctx.send(ConfigManager.get_config("strings")["error"]["no_permission"])
            RelevanceLogger.write_log_entry(f"cmd.reload - failed (no permission)", ctx.author.id, LogType.INFO)
            return
        
        await ctx.send(ConfigManager.get_config("strings")["response"]["reload"])
        RelevanceLogger.write_log_entry(f"cmd.reload - success, restarting", ctx.author.id, LogType.INFO)
        os.execv(sys.executable, ['python'] + sys.argv)

async def setup(bot):
    await bot.add_cog(ReloadCog(bot))
    RelevanceLogger.write_log_entry("cog.reload - loaded", "system", LogType.INFO)