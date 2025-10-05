from discord.ext import commands
from src.discord_bot.util.is_admin_on_guild import is_admin_on_guild
from src.config_manager import ConfigManager, StringManager, StringType
from src.discord_bot.logs.rl_log.log_handler import RelevanceLogger, LogType
from src.discord_bot.util.shutdown_protocol import shutdown_protocol
import os, sys

class ReloadCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reload.admin_only = True

    @commands.command(name='reload', help='Startet den Discord-Bot neu.')
    @commands.dm_only()
    async def reload(self, ctx):
        if not await is_admin_on_guild(self.bot, ctx.author.id):
            await ctx.send(StringManager.get_string(StringType.ERROR, "error.no_permission"))
            RelevanceLogger.write_log_entry(f"cmd.reload - failed (no permission)", ctx.author, LogType.INFO)
            return
        
        await ctx.send(StringManager.get_string(StringType.PROCESSING, "response.reload.start"))
        # Respond after reload
        ConfigManager.merge_config(module="discord_bot", new_data={"reload_response": {"waiting_for_response": True,"user": ctx.author.id}})
        RelevanceLogger.write_log_entry(f"cmd.reload - success, restarting", ctx.author, LogType.INFO)
        shutdown_protocol()
        os.execv(sys.executable, [sys.executable] + sys.argv)

async def setup(bot):
    await bot.add_cog(ReloadCog(bot))