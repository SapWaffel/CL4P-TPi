from discord.ext import commands 
import os
import discord
from src.config_manager import ConfigManager, StringManager, StringType
from src.discord_bot.util.is_admin_on_guild import is_admin_on_guild
from src.discord_bot.logs.rl_log.log_handler import RelevanceLogger, LogType

class PrintLogCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.print_log.admin_only = True

    @commands.command(name='print_log', help='Sendet die Log-Datei als Anhang.')
    @commands.dm_only()
    async def print_log(self, ctx):
        if not await is_admin_on_guild(self.bot, ctx.author.id):
            await ctx.send(StringManager.get_string(StringType.ERROR, "error.no_permission"))
            RelevanceLogger.write_log_entry(f"cmd.print_log - failed (no permission)", ctx.author.id, LogType.INFO)
            return
        
        
        log_dir = './src/discord_bot/logs/rl_log'
        log_files = [f for f in os.listdir(log_dir) if os.path.isfile(os.path.join(log_dir, f))]
        # no log files
        if not log_files:
            await ctx.send(StringManager.get_string(StringType.WARNING, "response.print_log.no_files"))
            RelevanceLogger.write_log_entry(f"cmd.print_log - failed (no log files)", ctx.author.id, LogType.INFO)
            return
        log_files.sort() 
        log_file_paths = [os.path.join(log_dir, f) for f in log_files]
        try:
            await ctx.send(files=[discord.File(fp) for fp in log_file_paths])
        except Exception as e:
            await ctx.send(StringManager.get_string(StringType.ERROR, "response.print_log.error", error=str(e)))
        return
    
async def setup(bot):
    await bot.add_cog(PrintLogCog(bot))